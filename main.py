import time , sys , numpy , cv2
import numpy as np
import imutils
import smtplib

import securityDetails

def sendEmail( alertLevel , msg ):

	FROM = securityDetails.fromEmail 
	TO = securityDetails.toEmail

	message = """From: %s\nTo: %s\nSubject: %s\n\n%s
    """ % (FROM, ", ".join(TO) , alertLevel , msg )

	try:
		server = smtplib.SMTP( "smtp.gmail.com" , 587 )
		server.ehlo()
		server.starttls()
		server.login( FROM , securityDetails.w_PASS )
		server.sendmail( FROM , TO , msg )
		server.close()
		print('sent email')
	except:
		print('failed to send email')

class TenvisVideo():

	def __init__( self , w_IP , w_Port , w_UN , w_Pass ):

		self.feed_url = "http://" + w_IP + ":" + w_Port + "/vjpeg.v?user=" + w_UN + "&pwd=" + w_Pass
		print self.feed_url

		self.startMotionTime = None
		self.totalMotionTime = 0
		self.totalMotionAcceptable = 25
		self.alertLevel = 0
		self.alertLevelAcceptable = 3
		
		self.w_Capture = cv2.VideoCapture(self.feed_url)
		self.fgbg = cv2.BackgroundSubtractorMOG2()

		self.motionTracking2()

	def cleanup(self):
		self.w_Capture.release()
		cv2.destroyAllWindows()

	def backgroundSubtractor( self ):

		while(1):

			ret , frame = self.w_Capture.read()
			fgmask = self.fgbg.apply( frame )

			cv2.imshow( 'Background Subtractor' , fgmask )
			k = cv2.waitKey(30) & 0xff
			if k == 27:
				break

		self.cleanup()
		
	def backgroundSubtractorGMG( self ):

		while(1):
			ret, frame = self.w_Capture.read()
			fgmask = self.fgbg.apply(frame)

			cv2.imshow('Background Subtractor - GMG',fgmask)

			k = cv2.waitKey(30) & 0xff
			if k == 27:
				break

		self.cleanup()

	def motionTracking( self ):

		firstFrame = None
		min_area = 500

		while True:

			( grabbed , frame ) = self.w_Capture.read()
			text = "No Motion"

			if not grabbed:
				break

			frame = imutils.resize( frame , width = 500 )
			gray = cv2.cvtColor( frame , cv2.COLOR_BGR2GRAY )
			gray = cv2.GaussianBlur( gray , ( 21 , 21 ) , 0 )

			if firstFrame is None:
				firstFrame = gray
				continue


			frameDelta = cv2.absdiff( firstFrame , gray )
			thresh = cv2.threshold( frameDelta , 25 , 255 , cv2.THRESH_BINARY )[1]
			( cnts , _ ) = cv2.findContours( thresh.copy() , cv2.RETR_EXTERNAL , cv2.CHAIN_APPROX_SIMPLE )

			for c in cnts:

				if cv2.contourArea( c ) < min_area:
					continue

				( x , y , w , h ) = cv2.boundingRect( c )
				cv2.rectangle( frame , ( x , y ) , ( x + w , y + h ) , ( 0 , 255 , 0 ) , 2 )
				text = "Motion Detected"


			cv2.putText( frame , "Room Status: {}".format(text) , ( 10 , 20 ) , cv2.FONT_HERSHEY_SIMPLEX , 0.5 , ( 0 , 0 , 255 ) , 2 )

			cv2.imshow( "Security Feed" , frame )
			cv2.imshow( "Thresh" , thresh )
			cv2.imshow( "Frame Delta" , frameDelta )


			k = cv2.waitKey(30) & 0xff
			if k == 27:
				break

		
		self.cleanup()

	def motionTracking2( self ):

		avg = None
		firstFrame = None

		min_area = 500
		delta_thresh = 5

		motionCounter = 0
		min_motion_frames = 1

		while True:

			( grabbed , frame ) = self.w_Capture.read()
			text = "No Motion"

			if not grabbed:
				break

			frame = imutils.resize( frame , width = 500 )
			gray = cv2.cvtColor( frame , cv2.COLOR_BGR2GRAY )
			gray = cv2.GaussianBlur( gray , ( 21 , 21 ) , 0 )

			if firstFrame is None:
				firstFrame = gray
				continue

			if avg is None:
				avg = gray.copy().astype("float")
				continue

			cv2.accumulateWeighted( gray , avg , 0.5 )
			frameDelta = cv2.absdiff( gray , cv2.convertScaleAbs(avg) )

			thresh = cv2.threshold( frameDelta , delta_thresh , 255 , cv2.THRESH_BINARY )[1]
			thresh = cv2.dilate( thresh , None , iterations=2 )
			(cnts, _) = cv2.findContours( thresh.copy() , cv2.RETR_EXTERNAL , cv2.CHAIN_APPROX_SIMPLE )

			for c in cnts:

				if cv2.contourArea( c ) < min_area:
					continue

				(x, y, w, h) = cv2.boundingRect(c)
				cv2.rectangle( frame , ( x , y ) , ( x + w , y + h ) , ( 0, 255 , 0 ) , 2 )
				text = "Motion"
				
				if self.startMotionTime is None:
					self.startMotionTime = time.time()


			cv2.putText( frame , "Room Status: {}".format(text) , ( 10 , 20 ) , cv2.FONT_HERSHEY_SIMPLEX , 0.5 , (0, 0, 255) , 2 )

			if text == "Motion":

				motionCounter += 1

				if motionCounter >= min_motion_frames:

					done = time.time()
					totalMotionTime = done - self.startMotionTime
					totalMotionTime = int(totalMotionTime) % 60
					self.totalMotionTime = self.totalMotionTime + totalMotionTime

					cv2.imshow( "Security Feed" , frame )
					cv2.imshow( "Thresh" , thresh )
					cv2.imshow( "Frame Delta" , frameDelta )

					motionCounter = 0
					

			else:
				motionCounter = 0


			if self.totalMotionTime > self.totalMotionAcceptable:
				self.alertLevel = self.alertLevel + 1
				self.totalMotionTime = 0
				self.startMotionTime = None
				
			if self.alertLevel > self.alertLevelAcceptable:
				sMesg = "haley is moving ALERT_LEVEL = " + str(self.alertLevel)
				sendEmail( "ALERT"  , sMesg )	
				self.alertLevel = 0

			k = cv2.waitKey(30) & 0xff
			if k == 27:
				break
			

		self.cleanup()




myTV = TenvisVideo( securityDetails.w_IP , securityDetails.w_PORT , securityDetails.w_USER , securityDetails.w_PASS )

