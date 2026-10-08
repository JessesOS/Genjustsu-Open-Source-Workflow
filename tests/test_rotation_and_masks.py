import sys,tempfile,unittest
from pathlib import Path
from unittest import mock
from PIL import Image
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import pipeline,raw_masks

class Frame:
    def __init__(self,rotation):self.rotation=rotation
    def to_image(self):
        img=Image.new('RGB',(40,20),'black');img.putpixel((0,0),(255,0,0));return img

class UprightTest(unittest.TestCase):
    def test_untagged_frame_is_unchanged(self):
        self.assertEqual(pipeline.upright(Frame(0)).size,(40,20))
    def test_phone_rotation_tag_is_applied(self):
        img=pipeline.upright(Frame(-90))
        self.assertEqual(img.size,(20,40))
        # -90 displays as a quarter turn clockwise: top-left moves to top-right
        self.assertEqual(img.getpixel((19,0)),(255,0,0))

class SegmentSubjectTest(unittest.TestCase):
    def fake(self,missing_on):
        calls=[]
        def segment_raw(video,folder,prompt='person'):
            calls.append(Path(video).name);out=Path(folder)/'raw-masks';out.mkdir(exist_ok=True)
            for i in range(2 if Path(video).name in missing_on else 0,5):(out/f'mask_{i:05d}.png').write_bytes(b'x')
            return out
        return calls,segment_raw
    def run_case(self,prompt,missing_on=()):
        calls,fn=self.fake(missing_on)
        with tempfile.TemporaryDirectory() as d, mock.patch.object(raw_masks,'segment_raw',fn):
            try:return calls,pipeline.segment_subject(Path(d),prompt,5,lambda s:None)[1]
            except ValueError as e:return calls,e
    def test_generic_prompt_uses_depth(self):
        self.assertEqual(self.run_case('person'),(['depth.mp4'],'depth'))
    def test_incomplete_depth_falls_back_to_original(self):
        self.assertEqual(self.run_case('person',('depth.mp4',)),(['depth.mp4','original.mp4'],'original RGB'))
    def test_specific_prompt_uses_original(self):
        self.assertEqual(self.run_case('man in grey sweatshirt'),(['original.mp4'],'original RGB'))
    def test_incomplete_everywhere_is_an_error(self):
        calls,result=self.run_case('person',('depth.mp4','original.mp4'))
        self.assertIsInstance(result,ValueError)

if __name__=='__main__':unittest.main()
