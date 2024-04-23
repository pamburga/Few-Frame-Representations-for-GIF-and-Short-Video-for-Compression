from mvextractor.videocap import VideoCap
import subprocess
import numpy as np
import ffmpeg

def convert_to_h264(input_path, output_path):
    """
    Converts a WebP or GIF file to H264-encoded MP4 format using FFmpeg.
    """
    cmd = f"ffmpeg -y -i {input_path} -c:v libx264 -preset medium -crf 23 -pix_fmt yuv420p {output_path}"
    subprocess.run(cmd, shell=True, check=True)

def reconstruct_frame(i_frame, motion_vectors, prev_frame):
    """
    Reconstructs a frame from an I frame, its motion vectors, and the previous frame using FFmpeg.
    """
    # Construct a motion vector array from the motion vectors
    mv_array = np.zeros((i_frame.shape[0] // 16, i_frame.shape[1] // 16, 2), dtype=np.float32)
    mv_array[..., 0] = motion_vectors[..., 0].ravel()
    mv_array[..., 1] = motion_vectors[..., 1].ravel()

    # Convert the frames to the required format
    i_frame = cv2.cvtColor(i_frame, cv2.COLOR_BGR2YUV_I420)
    prev_frame = cv2.cvtColor(prev_frame, cv2.COLOR_BGR2YUV_I420)

    # Reconstruct the frame using FFmpeg's mo
    .tion compensation filter
    reconstructed_frame = ffmpeg.input("pipe:", format="rawvideo", pix_fmt="yuv420p", s=f"{i_frame.shape[1]}x{i_frame.shape[0]}")
    reconstructed_frame = ffmpeg.filter(reconstructed_frame, "mcompensate", motion_vector=mv_array)
    reconstructed_frame = ffmpeg.output(reconstructed_frame, "pipe:", format="rawvideo", pix_fmt="yuv420p")
    reconstructed_frame = reconstructed_frame.run(input_data=i_frame.tobytes())[0]

    # Convert the reconstructed frame back to BGR format
    reconstructed_frame = np.frombuffer(reconstructed_frame, dtype=np.uint8)
    reconstructed_frame = reconstructed_frame.reshape((i_frame.shape[0] * 3 // 2, i_frame.shape[1]))
    reconstructed_frame = cv2.cvtColor(reconstructed_frame, cv2.COLOR_YUV2BGR_I420)

    return reconstructed_frame


convert_to_h264("sample.gif", "stream.mp4")

video = VideoCap()
success = video.open("stream.mp4")

params = []

prev_frame = None
i_frame = None
motion_vectors = None
if success:
    while video.grab():
        success, frame, motion_data, frame_type, timestamp = video.retrieve()

        if success:
            if frame_type == 'I':
                if prev_frame is not None:
                    params.append({"frame": prev_frame, "motion_vectors": motion_vectors})
                prev_frame = frame
                i_frame = frame
                motion_vectors = motion_data
            elif frame_type == 'P':
                if i_frame is not None:
                    reconstructed_frame = reconstruct_frame(i_frame, motion_vectors, prev_frame)
                    params.append({"frame": reconstructed_frame, "motion_vectors": motion_data})
                    prev_frame = reconstructed_frame
    video.release()

    # Save the reconstructed video to a file
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    writer = cv2.VideoWriter("reconstructed.mp4", fourcc, 30.0, (prev_frame.shape[1], prev_frame.shape[0]))
    for data in params:
        frame = data["frame"]
        writer.write(frame)
    writer.release()
else:
    print("Video read error!!")

