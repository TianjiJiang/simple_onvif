from onvif import ONVIFCamera
import cv2
import math

class Onvif_Camera:
    def __init__(self, ip, port ,user, pwd):
        self.ip = ip
        self.port = port
        self.user = user
        self.pwd = pwd

        self.Is_ptz_init = False

        # Connect to camera
        self.cam = ONVIFCamera(self.ip, self.port, self.user, self.pwd)
        print('Camera connected')

        # Create media service object
        self.media = self.cam.create_media_service()

    def ptz_init(self):
        pass

        # Create ptz service object
        self.ptz = self.cam.create_ptz_service()

        # Get target profile
        media_profile = self.media.GetProfiles()[0]

        # Get PTZ configuration options for getting continuous move range
        self.rel_move_request = self.ptz.create_type('GetConfigurationOptions')
        self.rel_move_request.ConfigurationToken = media_profile.PTZConfiguration.token
        ptz_configuration_options = self.ptz.GetConfigurationOptions(self.rel_move_request)

        # Get range of pan and tilt
        self.XMAX = ptz_configuration_options.Spaces.RelativePanTiltTranslationSpace[0].XRange.Max
        self.XMIN = ptz_configuration_options.Spaces.RelativePanTiltTranslationSpace[0].XRange.Min
        self.YMAX = ptz_configuration_options.Spaces.RelativePanTiltTranslationSpace[0].YRange.Max
        self.YMIN = ptz_configuration_options.Spaces.RelativePanTiltTranslationSpace[0].YRange.Min
        # print(XMAX, YMAX, XMIN, YMIN)

        self.rel_move_request = self.ptz.create_type('RelativeMove')
        self.rel_move_request.ProfileToken = media_profile.token
        if self.rel_move_request.Translation is None:
            self.rel_move_request.Translation = self.ptz.GetStatus({'ProfileToken': media_profile.token}).Position


    def move(self, x, y):
        if not self.Is_ptz_init:
            self.ptz_init()
        '''
        x in [XMIN*2, XMAX*2], sign represent direction
        y in [YMIN*2, YMAX*2], sign represent direction
        '''
        if abs(x) > (self.XMAX - self.XMIN):
            print("WARNNING: abs(x) should not larger than {}.".formar(self.XMAX - self.XMIN))
        if abs(y) > (self.YMAX - self.YMIN):
            print("WARNNING: abs(y) should not larger than {}.".formar(self.YMAX - self.YMIN))

        self.rel_move_request.Translation.PanTilt.x = x
        self.rel_move_request.Translation.PanTilt.y = y

        try:
            self.ptz.RelativeMove(self.rel_move_request)
            return True
        except:
            print("Maybe your step is out of range")
            return False

    def get_rtsp_uri(self):
        media_profile = self.media.GetProfiles()
        token = media_profile[0].token
        obj = self.media.create_type('GetStreamUri')
        obj.StreamSetup = {'Stream': 'RTP-Unicast', 'Transport': {'Protocol': 'RTSP'}}
        obj.ProfileToken = token
        res_uri = self.media.GetStreamUri(obj)['Uri']
        return res_uri


    def get_opencv_VideoCapture(self):
        uri = self.get_rtsp_uri()
        uri = uri.replace('rtsp://', 'rtsp://{}:{}@'.format(self.user, self.pwd))
        print(uri)
        return cv2.VideoCapture(uri)

if __name__ == "__main__":
    onvif_cam = Onvif_Camera('192.168.1.101', 80, 'admin', '123456')
    cam = onvif_cam.get_opencv_VideoCapture()
    ret, img = cam.read()
    cv2.namedWindow('a', 0)
    for i in range(100000):
        if not ret:
            break
        cv2.imshow('a', img)
        cv2.waitKey(1)
        if i % 30 == 0:
            print('move ({}, {})'.format(math.sin(i/90*math.pi), math.cos(i/90*math.pi)))
            onvif_cam.move(math.sin(i/90*math.pi), math.cos(i/90*math.pi))
