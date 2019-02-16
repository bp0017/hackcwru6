import numpy as np
import os
import csv
import imutils
from imutils.object_detection import non_max_suppression
import argparse
import time
import cv2
 
def getPlate(CONFIDENCE = 0.5,PADDINGX = 100,PADDINGY = 50,newW = 512, newH =288):
	filepath  = '/home/bp0017/Documents/hackathon/jesse_data/benchmarks-master/endtoend/us/wts-lg-000051.jpg'
	image = cv2.imread(filepath)#np.asarray(Image.open(filepath).convert("L")) #I like pillow's image opening method better
	orig = image.copy()
	(H, W) = image.shape[:2]

	#16:9 aspect ratio. must be multiples of 32. Manual
	rW = W / float(newW)
	rH = H / float(newH)
	image = cv2.resize(image, (newW, newH))
	(H, W) = image.shape[:2]

	layerNames = ["feature_fusion/Conv_7/Sigmoid", "feature_fusion/concat_3"]

	net = cv2.dnn.readNet('/home/bp0017/Documents/east/opencv-text-detection/frozen_east_text_detection.pb') #using EAST text detect

	# construct a blob from the image and then perform a forward pass of
	# the model to obtain the two output layer sets
	blob = cv2.dnn.blobFromImage(image, 1.0, (W, H),
		(123.68, 116.78, 103.94), swapRB=True, crop=False) #config from https://www.pyimagesearch.com/2018/08/20/opencv-text-detection-east-text-detector/
	net.setInput(blob)
	(scores, geometry) = net.forward(layerNames) #forward pass
	(numRows, numCols) = scores.shape[2:4]
	rects = []
	confidences = []
	 
	# loop over the number of rows
	for y in range(0, numRows):
		# extract the scores (probabilities), followed by the geometrical
		# data used to derive potential bounding box coordinates that
		# surround text
		scoresData = scores[0, 0, y]
		xData0 = geometry[0, 0, y]
		xData1 = geometry[0, 1, y]
		xData2 = geometry[0, 2, y]
		xData3 = geometry[0, 3, y]
		anglesData = geometry[0, 4, y]

		# loop over the number of columns
		for x in range(0, numCols):
			# if our score does not have sufficient probability, ignore it
			if scoresData[x] <CONFIDENCE:
				continue
	 
			# compute the offset factor as our resulting feature maps will
			# be 4x smaller than the input image
			(offsetX, offsetY) = (x * 4.0, y * 4.0)
	 
			# extract the rotation angle for the prediction and then
			# compute the sin and cosine
			angle = anglesData[x]
			cos = np.cos(angle)
			sin = np.sin(angle)
	 
			# use the geometry volume to derive the width and height of
			# the bounding box
			h = xData0[x] + xData2[x]
			w = xData1[x] + xData3[x]
	 
			# compute both the starting and ending (x, y)-coordinates for
			# the text prediction bounding box
			endX = int(offsetX + (cos * xData1[x]) + (sin * xData2[x]))
			endY = int(offsetY - (sin * xData1[x]) + (cos * xData2[x]))
			startX = int(endX - w)
			startY = int(endY - h)
	 
			# add the bounding box coordinates and probability score to
			# our respective lists
			rects.append((startX, startY, endX, endY))
			confidences.append(scoresData[x])

	# apply non-maxima suppression to suppress weak, overlapping bounding
	# boxes
	boxes = non_max_suppression(np.array(rects), probs=confidences)
	 
	# loop over the bounding boxes
	cropped_plates = []
	for (startX, startY, endX, endY) in boxes:
		# scale the bounding box coordinates based on the respective
		# ratios
		startX = int(startX * rW)
		startY = int(startY * rH)
		endX = int(endX * rW)
		endY = int(endY * rH)

		#cv2.rectangle(orig, (startX, startY), (endX, endY), (0, 255, 0), 2)
		#print((startX, startY), (endX, endY))
		cpy = orig.copy()
		cropped = cpy[startY-PADDINGX:endY+PADDINGX,startX-PADDINGY:endX+PADDINGY]
		x,y,depth = cropped.shape
		if (x and y and depth): #if it's not in the image, don't show it
			#cv2.imshow("cropped", cropped)
			#cv2.waitKey(0)
			cropped_plates.append(cropped)



	for img in cropped_plates:
		cv2.imshow("Text Detection", img)
		cv2.waitKey(0)

		return cropped_plates

