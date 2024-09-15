import simpleaudio as sa
#play wav file 
wave_obj = sa.WaveObject.from_wave_file("/mnt/88c49251-2b3d-489c-be49-24b3d296dd4b/project_decdo/Promodomo/rest.wav")
play_obj = wave_obj.play()
play_obj.wait_done()  # Wait for sound to finish playing