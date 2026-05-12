from geminiaiapp.try_on import VirtualTryOn

vto= VirtualTryOn()
person_image=r"C:\Users\MRH RAFI\Pictures\Screenshots\Screenshot 2026-05-06 100202.png"
dress_image=r"C:\Users\MRH RAFI\Downloads\red bride.jpg"

result=vto.perform_try_on(person_image, dress_image)

result.show()