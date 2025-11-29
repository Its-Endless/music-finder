import sounddevice as sd
import soundfile as sf
import numpy as np

def record_audio(duration=6, sample_rate=44100, output_file="query.wav"):
    print(f"🎤 Recording for {duration} seconds...")

    audio = sd.rec(
        int(duration * sample_rate),
        samplerate=sample_rate,
        channels=1,
        dtype="float32"
    )
    sd.wait()

    audio = np.squeeze(audio)

    sf.write(output_file, audio, sample_rate)

    print(f"✔ Saved recording to {output_file}")


if __name__ == "__main__":
    record_audio()