

from manager.models import *


def update_history_data():
    try:
        aus = AudioStory.objects.filter(audioStoryType=True).all()
        for a in aus:
            try:
                with transaction.atomic():
                    a.name = a.storyUuid.name
                    a.bgIcon = a.storyUuid.faceIcon
                    a.save()
            except Exception as e:
                print(str(e))
    except Exception as e:
        print(str(e))
    print("成功")


if __name__ == "__main__":
    update_history_data()
