import cv2
import numpy as np
import os
import math
import matplotlib.pyplot as plt
from matplotlib.ticker import MultipleLocator

# -------------------- CAR CLASS --------------------
class Car:
    def __init__(self, i, xi, yi, max_age):
        self.i = i
        self.x = xi
        self.y = yi
        self.tracks = []
        self.done = False
        self.state = '0'
        self.age = 0
        self.max_age = max_age
        self.dir = None
        self.frames_crossed = 0

    def getId(self): return self.i
    def getX(self): return self.x
    def getY(self): return self.y
    def updateCoords(self, xn, yn):
        self.age = 0
        self.tracks.append([self.x, self.y])
        self.x = xn
        self.y = yn
        self.frames_crossed += 1
    def setDone(self): self.done = True
    def timedOut(self): return self.done

    def going_UP(self, mid_start, mid_end):
        if len(self.tracks) >= 2 and self.state == '0':
            if self.tracks[-1][1] < mid_end and self.tracks[-2][1] >= mid_end:
                self.state = '1'
                self.dir = 'up'
                return True
        return False

    def going_DOWN(self, mid_start, mid_end):
        if len(self.tracks) >= 2 and self.state == '0':
            if self.tracks[-1][1] > mid_start and self.tracks[-2][1] <= mid_start:
                self.state = '1'
                self.dir = 'down'
                return True
        return False

    def age_one(self):
        self.age += 1
        if self.age > self.max_age:
            self.done = True
        return True

# -------------------- UTILS --------------------
def estimate_aqi(car_count, truck_count):
    car_emission_rate = 120
    truck_emission_rate = 900
    total_emissions = car_count * car_emission_rate + truck_count * truck_emission_rate
    aqi = min(int(total_emissions / 100), 500)
    quality = ["Good", "Moderate", "Unhealthy for Sensitive Groups", "Unhealthy", "Very Unhealthy", "Hazardous"]
    return (aqi, quality[min(aqi // 50, 5)])

def euclidean_distance(x1, y1, x2, y2):
    return math.hypot(x1 - x2, y1 - y2)

# -------------------- MAIN FUNCTION --------------------
def process_video(video_path):
    os.makedirs('detected', exist_ok=True)

    cap = cv2.VideoCapture(video_path)
    fgbg = cv2.createBackgroundSubtractorMOG2(detectShadows=False, history=200, varThreshold=90)
    fps = cap.get(cv2.CAP_PROP_FPS)
    kernelOp = np.ones((3, 3), np.uint8)
    kernelCl = np.ones((11, 11), np.uint8)

    cars = []
    max_p_age = 5
    pid = 1

    cnt_up = cnt_down = cnt_car = cnt_truck = 0
    line_up = 400
    line_down = 250
    up_limit = 230
    down_limit = int(4.5 * (500 / 5))
    pixel_distance = abs(line_down - line_up)
    meters_per_pixel = 8.0 / pixel_distance
    speed_limit = 100
    speeds = {}
    overspeeding_ids = []
    aqi_history = []

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret: break
        frame = cv2.resize(frame, (900, 500))
        fgmask = fgbg.apply(frame)

        _, imBin = cv2.threshold(fgmask, 200, 255, cv2.THRESH_BINARY)
        mask = cv2.morphologyEx(imBin, cv2.MORPH_OPEN, kernelOp)
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernelCl)

        contours0, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        detected_centroids = []

        for cnt in contours0:
            area = cv2.contourArea(cnt)
            if area > 300:
                m = cv2.moments(cnt)
                if m['m00'] == 0: continue
                cx = int(m['m10'] / m['m00'])
                cy = int(m['m01'] / m['m00'])
                x, y, w, h = cv2.boundingRect(cnt)
                if up_limit < cy < down_limit:
                    detected_centroids.append((cx, cy, x, y, w, h))

        for cx, cy, x, y, w, h in detected_centroids:
            matched = False
            for car in cars:
                if euclidean_distance(cx, cy, car.getX(), car.getY()) < 50:
                    car.updateCoords(cx, cy)
                    matched = True
                    if not hasattr(car, 'counted') and (car.going_UP(line_down, line_up) or car.going_DOWN(line_down, line_up)):
                        direction = car.dir
                        if direction == 'up': cnt_up += 1
                        else: cnt_down += 1

                        area = w * h
                        aspect_ratio = w / float(h)
                        label = "Truck" if area > 30000 or (area > 5000 and aspect_ratio < 1.2) else "Car"
                        cnt_car += label == "Car"
                        cnt_truck += label == "Truck"
                        car.counted = True

                        speed = ((pixel_distance * meters_per_pixel) / (car.frames_crossed / fps)) * 3.6
                        if 0 < speed < 180:
                            speeds[car.getId()] = round(speed, 2)
                            if speed > speed_limit:
                                overspeeding_ids.append(car.getId())
                                vehicle_img = frame[y:y+h, x:x+w]
                                cv2.imwrite(f"detected/overspeed_vehicle_{car.getId()}.jpg", vehicle_img)
                    break

            if not matched:
                cars.append(Car(pid, cx, cy, max_p_age))
                pid += 1

        for car in cars[:]:
            car.age_one()
            if car.timedOut():
                cars.remove(car)

        aqi, _ = estimate_aqi(cnt_car, cnt_truck)
        aqi_history.append(aqi)

    cap.release()
    cv2.destroyAllWindows()

    estimated_aqi, air_quality = estimate_aqi(cnt_car, cnt_truck)
    total_vehicles = cnt_car + cnt_truck

    with open('aqi_report.txt', 'w') as f:
        f.write(f"Total Vehicles: {total_vehicles}\n")
        f.write(f"Estimated AQI: {estimated_aqi}\n")
        f.write(f"Air Quality: {air_quality}\n")
        f.write(f"Overspeeding Vehicle IDs: {overspeeding_ids}\n")

    return {
        "total_vehicles": total_vehicles,
        "estimated_aqi": estimated_aqi,
        "air_quality": air_quality,
        "overspeeding_ids": overspeeding_ids
    }
