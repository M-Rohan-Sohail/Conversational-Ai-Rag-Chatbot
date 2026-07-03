import asyncio
import edge_tts
import pygame

pygame.mixer.init()

async def tts_to_file(text, filename="output.mp3", voice="en-US-AriaNeural"):
    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(filename)

def play_audio(filename="output.mp3"):
    pygame.mixer.music.load(filename)
    pygame.mixer.music.play()
    while pygame.mixer.music.get_busy():
        pygame.time.Clock().tick(10)
    
    # Release the file lock so it can be handled or deleted safely
    try:
        pygame.mixer.music.unload()
    except AttributeError:
        pass