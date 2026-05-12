from django.shortcuts import render

# Create your views here.
import replicate
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.conf import settings
from .models import Dress, TryOn

client = replicate.Client(api_token=settings.REPLICATE_API_TOKEN)


@api_view(['POST'])
def try_on(request):
    user_image = request.FILES.get("user_image")
    dress_id = request.data.get("dress_id")

    if not user_image or not dress_id:
        return Response({"error": "Missing data"}, status=400)

    dress = Dress.objects.get(id=dress_id)

    # ⚠️ IMPORTANT: Replicate needs PUBLIC URL
    # For testing, use ngrok OR manually upload images online

    user_image_url = request.build_absolute_uri(user_image.name)
    dress_image_url = request.build_absolute_uri(dress.image.url)

    try:
        output = client.run(
            "viktorfa/oot_diffusion_with_mask:c890e02d8180bde7eeed1a138217ee154d8cdd8769a29f02bd51fea33d268385",
            input={
                "try_on": True,
                "garment": dress_image_url,
                "person_image": user_image_url,
                "num_steps": 16
            }
        )

        result_url = output[0].url

        tryon = TryOn.objects.create(
            user_image=user_image,
            dress=dress,
            result_image=result_url
        )

        return Response({
            "result": result_url,
            "id": tryon.id
        })

    except Exception as e:
        return Response({"error": str(e)}, status=500)