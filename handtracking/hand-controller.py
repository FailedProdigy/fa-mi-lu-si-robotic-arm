import asyncio
from dataclasses import asdict, dataclass

import cv2
import mediapipe.python.solutions.drawing_styles as mp_drawing_styles
import mediapipe.python.solutions.drawing_utils as mp_drawing
import mediapipe.python.solutions.hands as mp_hands
import numpy as np
import math
from bleak import BleakClient, BleakScanner

uart_service_uuid = "6E400001-B5A3-F393-E0A9-E50E24DCCA9E"
rx_uuid = "6E400003-B5A3-F393-E0A9-E50E24DCCA9E"
tx_uuid = "6E400002-B5A3-F393-E0A9-E50E24DCCA9E"


def lerp(a, b, t):
    return (1 - t) * a + t * b


def landmark_to_np(item):
    return np.array([item.x, item.y, item.z])


def angle_between(v1, v2):
    cos_angle = np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2))
    return np.arccos(np.clip(cos_angle, -1.0, 1.0))


def distance_between(v1, v2):
    return np.linalg.norm(v1 - v2)


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
        if device.name == "mpy-uart":
            return device

    print("Couldn't find robotic arm")
    return None


async def send_data(pico: BleakClient):
    if pico and pico.is_connected:
        try:
            for motor_name, value in asdict(robot).items():
                await pico.write_gatt_char(tx_uuid, f"{motor_name}:{value}".encode())
                print(f"Sent value {motor_name}:{value}")
        except Exception as e:
            print(f"Failed to send data {e}")


async def process_frame(hands, frame):
    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = await asyncio.to_thread(
        hands.process, frame_rgb
    )  # Offload processing to a thread

    return results


async def run_handtracking():
    cap = cv2.VideoCapture(index=0)

    with mp_hands.Hands(
        model_complexity=0,
        max_num_hands=1,
        min_detection_confidence=0.5,
        min_tracking_confidence=0.5,
    ) as hands:
        while cap.isOpened():
            success, frame = cap.read()
            if not success:
                print("Ignoring empty camera frame...")
                await asyncio.sleep(0.01)
                continue

            # Check the frame for hands
            results = await process_frame(hands, frame)

            if results.multi_hand_landmarks:
                for hand_landmarks in results.multi_hand_landmarks:
                    # Draw the hand annotations on the image
                    mp_drawing.draw_landmarks(
                        image=frame,
                        landmark_list=hand_landmarks,
                        connections=mp_hands.HAND_CONNECTIONS,
                        landmark_drawing_spec=mp_drawing_styles.get_default_hand_landmarks_style(),
                        connection_drawing_spec=mp_drawing_styles.get_default_hand_connections_style(),
                    )

                    
                    wrist = landmark_to_np(
                        hand_landmarks.landmark[mp_hands.HandLandmark.WRIST]
                    )

                    robot.base = int((1 - wrist[0]) * 65535)
                    robot.bottom = int((1 - wrist[1]) * 65535)

            if results.multi_hand_world_landmarks:
                for hand_landmarks in results.multi_hand_world_landmarks:
                    index_finger_tip = landmark_to_np(
                        hand_landmarks.landmark[mp_hands.HandLandmark.INDEX_FINGER_TIP]
                    )
                    thumb_tip = landmark_to_np(
                        hand_landmarks.landmark[mp_hands.HandLandmark.THUMB_TIP]
                    )
                    pinky_mcp = landmark_to_np(
                        hand_landmarks.landmark[mp_hands.HandLandmark.PINKY_MCP]
                    )

                    # IMPORTANT : SWITCH TO CALCULATING THE SLOPE INSTEAD
                    robot.top = int(angle_between(pinky_mcp, np.where(np.arange(3) == 2, 0, pinky_mcp)) / (1/2 * math.pi) * 65535)

                    robot.hand = {
                        False: int(1/4 * 65535),
                        True: int(3/4 * 65535)
                    }.get(distance_between(index_finger_tip, thumb_tip) > 0.05)
                    
            # Display debug info
            frame = cv2.flip(frame, 1)
            cv2.putText(
                frame,  # Frame to draw on
                f"{robot}",  # Text to display
                (10, 30),  # Position (x, y)
                cv2.FONT_HERSHEY_SIMPLEX,  # Font
                0.5,  # Font size (scale)
                (0, 0, 0),  # Text color (BGR - green here)
                1,  # Thickness of the text
                cv2.LINE_AA,  # Line type for better rendering
            )

            await asyncio.to_thread(cv2.imshow, "Hand Tracking", frame)
            if cv2.waitKey(1) & 0xFF == ord("q"):
                break
            await asyncio.sleep(0.001)

    cap.release()
    cv2.destroyAllWindows()


async def main():
    pico_device = await find_device()
    if not pico_device:
        return
    async with BleakClient(pico_device) as pico:
        handtracking_task = asyncio.create_task(run_handtracking())

        async def sending_task():
            while not handtracking_task.done():
                await send_data(pico)

        await asyncio.gather(handtracking_task, asyncio.create_task(sending_task()))


if __name__ == "__main__":
    asyncio.run(main())
    # asyncio.run(run_handtracking())
