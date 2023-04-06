
import os
from fractions import Fraction
import av
from vidalign.utils.clip import Clip
from vidalign.utils.encoders import Encoder
from vidalign.utils.video import Video


class PyAVWriter:
    def __init__(self, output_path: str, codec: str, crf: int, frame_rate: float, width: int, height: int):
        # It's unclear to what precision is allowed for the frame rate, so start at
        # 32 bit and work down until we find a valid frame rate. Don't allow any
        # lower than 8 bit, as that might indicate further issues.
        max_exp = 32
        min_exp = 8
        exp = max_exp
        while True:
            try:
                self.container = av.open(output_path, mode='w')
                frame_rate = Fraction(frame_rate).limit_denominator(2**exp - 1)
                self.stream = self.container.add_stream(codec, rate=frame_rate)
                break
            except OverflowError as e:
                exp -= 1
                if exp < min_exp:
                    raise RuntimeError('Failed to find a valid frame rate') from e
        self.stream.width = width
        self.stream.height = height
        self.stream.pix_fmt = 'nv21'
        self.stream.options = {'crf': str(crf), 'preset': 'faster'}

    def write(self, frame):
        frame = av.VideoFrame.from_ndarray(frame, format='rgb24')
        for packet in self.stream.encode(frame):
            self.container.mux(packet)

    def release(self):
        # Flush stream
        for packet in self.stream.encode():
            self.container.mux(packet)

        # Close the file
        self.container.close()


class PyAV(Encoder):
    def __init__(self):
        super().__init__(
            'PyAV',
            {
                'vcodec': Encoder.EncParam('-encoding', 'h264', 'h264', 'Video codec. Try `ffmpeg -codecs` for a list of available codecs.'),
                'pix_fmt': Encoder.EncParam('-pix_fmt', 'yuv420p', 'yuv420p', 'Pixel format'),
                'crf': Encoder.EncParam('-crf', '18', '18', 'CRF. Lower values are better quality, but larger files.'),
            }
        )

    def output_path(self, video, clip, output_dir):
        path = self.get_clip_base_path(video, clip, output_dir)
        base = os.path.splitext(path)[0]
        path = f'{base}.mp4'
        return path

    def get_encode_command(self, video: Video, clip: Clip, output_dir: str):
        writer = None

        def _run_encode():
            nonlocal writer
            reader = video.reader
            abs_start_frame = video.rel_to_abs(clip.start_frame)
            abs_end_frame = video.rel_to_abs(clip.end_frame)
            reader.seek_absolute(abs_start_frame)

            writer = PyAVWriter(
                output_path=self.output_path(video, clip, output_dir),
                codec=self.enc_params['vcodec'].value,
                crf=int(self.enc_params['crf'].value),
                frame_rate=video.frame_rate,
                width=reader.width,
                height=reader.height,
            )

            while reader.current_frame < abs_end_frame:
                yield f'\rFrame {reader.current_frame} written'
                frame = reader.grab()
                writer.write(frame)
                reader.step()

            writer.release()

            yield f'\rDone writing {self.output_path(video, clip, output_dir)}'

        def _cancel_encode():
            if writer:
                writer.release()

        def _get_funcs():
            return _run_encode, _cancel_encode

        return _get_funcs