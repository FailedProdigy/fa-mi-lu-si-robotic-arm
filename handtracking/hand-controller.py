import asyncio
from dataclasses import asdict, dataclass

import cv2
import mediapipe as mp
from mediapipe import solutions
from mediapipe.framework.formats import landmark_pb2
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
import numpy as np
from bleak import BleakClient, BleakScanner

# uart_service_uuid = "6E400001-B5A3-F393-E0A9-E50E24DCCA9E"
# rx_uuid = "6E400003-B5A3-F393-E0A9-E50E24DCCA9E"
tx_uuid = "0000ffe1-0000-1000-8000-00805f9b34fb"


def landmark_to_np(item):
    return np.array([item.x, item.y, item.z])


def angle_between(v1, v2):
    cos_angle = np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2))
    return np.arccos(np.clip(cos_angle, -1.0, 1.0))


def distance_between(v1, v2):
    return np.linalg.norm(v1 - v2)


def draw_landmarks_on_image(rgb_image, detection_result):
    hand_landmarks_list = detection_result.hand_landmarks
    annotated_image = np.copy(rgb_image)

    # Loop through the detected hands to visualize.
    for idx in range(len(hand_landmarks_list)):
        hand_landmarks = hand_landmarks_list[idx]

        # Draw the hand landmarks.
        hand_landmarks_proto = landmark_pb2.NormalizedLandmarkList()
        hand_landmarks_proto.landmark.extend(
            [
                landmark_pb2.NormalizedLandmark(
                    x=landmark.x, y=landmark.y, z=landmark.z
                )
                for landmark in hand_landmarks
            ]
        )
        solutions.drawing_utils.draw_landmarks(
            annotated_image,
            hand_landmarks_proto,
            solutions.hands.HAND_CONNECTIONS,
            solutions.drawing_styles.get_default_hand_landmarks_style(),
            solutions.drawing_styles.get_default_hand_connections_style(),
        )
    return annotated_image


@dataclass
class Robot:
    base: int = 36463
    bottom: int = 44593
    middle: int = 18477
    top: int = 41390
    hand: int = 0  # uses 65535 / 2 as the threshold


robot = Robot()


async def find_device():
    devices = await BleakScanner.discover()

    for device in devices:
        if device.name == "HC-08":
            return device

    print("Couldn't find robotic arm")
    return None


async def send_data(pico: BleakClient):
    try:
        if pico and pico.is_connected:
            for motor_name, value in asdict(robot).items():  # type: ignore
                await pico.write_gatt_char(tx_uuid, f"{motor_name}:{value}\n".encode(), response=True)
                print(f"Sent value {motor_name}:{value}")
                # await asyncio.sleep(1)
    except Exception as e:
        print(f"Failed to send data {e}")


base_options = python.BaseOptions(model_asset_path="hand_landmarker.task")
options = vision.HandLandmarkerOptions(base_options=base_options, num_hands=1)
detector = vision.HandLandmarker.create_from_options(options)


async def process_frame(detector, frame_rgb):
    mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=frame_rgb)
    results = await asyncio.to_thread(
        detector.detect, mp_image
    )  # Offload processing to a thread

    return results


async def run_handtracking():
    cap = cv2.VideoCapture(index=0)

    while cap.isOpened():
        success, frame = cap.read()
        if not success:
            print("Ignoring empty camera frame...")
            await asyncio.sleep(0.01)
            continue

        image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        # Check the frame for hands
        result = await process_frame(detector, image)

        # Commented out the robot calculations for now, will move them later
        if result.hand_landmarks:
            for hand_landmark in result.hand_landmarks:
                wrist = landmark_to_np(
                    hand_landmark[solutions.hands.HandLandmark.WRIST]
                )

                robot.base = int((1 - wrist[0]) * 65535)
                robot.bottom = int((1 - wrist[1]) * 65535)

        if result.hand_world_landmarks:
            for hand_landmark in result.hand_world_landmarks:
                index_finger_tip = landmark_to_np(
                    hand_landmark[solutions.hands.HandLandmark.INDEX_FINGER_TIP]
                )
                thumb_tip = landmark_to_np(
                    hand_landmark[solutions.hands.HandLandmark.THUMB_TIP]
                )
                # pinky_mcp = landmark_to_np(
                #     hand_landmarks.landmark[solutions.hands.HandLandmark.PINKY_MCP]
                # )

                # IMPORTANT : SWITCH TO CALCULATING THE SLOPE INSTEAD
                # robot.top = int(angle_between(pinky_mcp, np.where(np.arange(3) == 2, 0, pinky_mcp)) / (1/2 * math.pi) * 65535)

                robot.hand = {
                    False: int(1 / 4 * 65535),
                    True: int(3 / 4 * 65535),
                }.get(bool(distance_between(index_finger_tip, thumb_tip) > 0.05), 0)

        # Draw the hands
        annotated_image = draw_landmarks_on_image(frame, result)
        # Display debug info
        annotated_image = cv2.flip(annotated_image, 1)

        cv2.putText(
            annotated_image,  # Frame to draw on
            f"{robot}",  # Text to display
            (10, 30),  # Position (x, y)
            cv2.FONT_HERSHEY_SIMPLEX,  # Font
            0.5,  # Font size (scale)
            (0, 0, 0),  # Text color (BGR - green here)
            1,  # Thickness of the text
            cv2.LINE_AA,  # Line type for better rendering
        )

        await asyncio.to_thread(cv2.imshow, "Hand Tracking", annotated_image)
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break
        await asyncio.sleep(0.001)

    cap.release()
    cv2.destroyAllWindows()


async def main():
    handtracking_task = asyncio.create_task(run_handtracking())

    async def sending_task(other_task):
        pico_device = await find_device()
        if not pico_device:
            return

        async with BleakClient(pico_device) as pico:
            while not other_task.done():
                await send_data(pico)

    await asyncio.gather(
        handtracking_task, asyncio.create_task(sending_task(handtracking_task))
    )


if __name__ == "__main__":
    asyncio.run(main())
    # asyncio.run(run_handtracking())
