import cv2
import argparse
import numpy as np

from PIL import Image

class yolov5():
    def __init__(self, confThreshold=0.5, nmsThreshold=0.5, objThreshold=0.5):
        with open('model/yolov5.txt', 'rt') as f:
            self.classes = f.read().rstrip('\n').split('\n')
        self.colors = [np.random.randint(0, 255, size=3).tolist() for _ in range(len(self.classes))]
        num_classes = len(self.classes)
        anchors = [[10, 13, 16, 30, 33, 23], [30, 61, 62, 45, 59, 119], [116, 90, 156, 198, 373, 326]]
        self.nl = len(anchors)
        self.na = len(anchors[0]) // 2
        self.no = num_classes + 5
        self.grid = [np.zeros(1)] * self.nl
        self.stride = np.array([8., 16., 32.])
        self.anchor_grid = np.asarray(anchors, dtype=np.float32).reshape(self.nl, -1, 2)
        self.inpWidth = 640
        self.inpHeight = 640
        self.net = cv2.dnn.readNet('model/yolov5s.onnx')
        self.confThreshold = confThreshold
        self.nmsThreshold = nmsThreshold
        self.objThreshold = objThreshold

    def is_marked(self, img_path):
        """Detect specific color for detect marked"""
        img = Image.open(img_path).convert('RGB')
        w, h = img.size
        for i in range(w):
            for j in range(h):
                r, g, b = img.getpixel((i, j))
                if r == 254 and g == 0 and b == 0:  # Detect Red Color
                    return True
        return False

    def _make_grid(self, nx=20, ny=20):
        xv, yv = np.meshgrid(np.arange(ny), np.arange(nx))
        return np.stack((xv, yv), 2).reshape((-1, 2)).astype(np.float32)

    def predict(self, file, obj=None):
        frame = cv2.imread(file)
        blob = cv2.dnn.blobFromImage(frame, 1 / 255.0, (self.inpWidth, self.inpHeight), [0, 0, 0], swapRB=True, crop=False)
        # Sets the input to the network
        self.net.setInput(blob)

        # Runs the forward pass to get output of the output layers
        outs = self.net.forward(self.net.getUnconnectedOutLayersNames())[0]

        # inference output
        outs = 1 / (1 + np.exp(-outs))   ###sigmoid
        row_ind = 0
        for i in range(self.nl):
            h, w = int(self.inpHeight/self.stride[i]), int(self.inpWidth/self.stride[i])
            length = int(self.na * h * w)
            if self.grid[i].shape[2:4] != (h,w):
                self.grid[i] = self._make_grid(w, h)

            outs[row_ind:row_ind+length, 0:2] = (outs[row_ind:row_ind+length, 0:2] * 2. - 0.5 + np.tile(self.grid[i],(self.na, 1))) * int(self.stride[i])
            outs[row_ind:row_ind+length, 2:4] = (outs[row_ind:row_ind+length, 2:4] * 2) ** 2 * np.repeat(self.anchor_grid[i],h*w, axis=0)
            row_ind += length
        if not obj:
            classes_names = []
            for detection in outs:
                scores = detection[5:]
                class_id = int(np.argmax(scores))
                confidence = scores[class_id]
                if confidence > self.confThreshold and detection[4] > self.objThreshold:
                    classes_names.append(self.classes[class_id])
            return classes_names  # Return all names object in the images
        else:
            frameHeight = frame.shape[0]
            frameWidth = frame.shape[1]
            ratioh, ratiow = frameHeight / self.inpHeight, frameWidth / self.inpWidth
            # Scan through all the bounding boxes output from the network and keep only the
            # ones with high confidence scores. Assign the box's class label as the class with the highest score.
            classIds = []
            confidences = []
            boxes = []
            for detection in outs:
                scores = detection[5:]
                classId = np.argmax(scores)
                confidence = scores[classId]
                if confidence > self.confThreshold and detection[4] > self.objThreshold:
                    center_x = int(detection[0] * ratiow)
                    center_y = int(detection[1] * ratioh)
                    width = int(detection[2] * ratiow)
                    height = int(detection[3] * ratioh)
                    left = int(center_x - width / 2)
                    top = int(center_y - height / 2)
                    classIds.append(classId)
                    confidences.append(float(confidence))
                    boxes.append([left, top, width, height])

            # Perform non maximum suppression to eliminate redundant overlapping boxes with
            # lower confidences.
            out_path = f"pictures/tmp/{hash(file)}.jpg"
            indices = cv2.dnn.NMSBoxes(boxes, confidences, self.confThreshold, self.nmsThreshold)
            out = False
            for i in indices:
                print(self.classes[int(classIds[int(i)])])
                if self.classes[int(classIds[int(i)])] == obj or (obj == 'vehicles' and (
                                    self.classes[int(classIds[int(i)])] == 'car'
                                    or self.classes[int(classIds[int(i)])] == 'truck'
                                    or self.classes[int(classIds[int(i)])] == 'bus')):
                    out = out_path
                    box = boxes[i]
                    left = box[0]
                    top = box[1]
                    width = box[2]
                    height = box[3]
                    frame = self.drawPred(frame, left, top, left + width, top + height)
            if out:
                cv2.imwrite(out_path, frame)
            return out 
            
    def drawPred(self, frame, left, top, right, bottom):
        # Draw a bounding box.
        cv2.rectangle(frame, (left, top), (right, bottom), (0, 0, 256), cv2.FILLED)
        return frame
