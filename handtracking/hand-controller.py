import cv2

import asyncio
from bleak import BleakScanner, BleakClient

import mediapipe.python.solutions.hands as mp_hands
import mediapipe.python.solutions.drawing_utils as mp_drawing
import mediapipe.python.solutions.drawing_styles as mp_drawing_styles

uart_service_uuid = "6E400001-B5A3-F393-E0A9-E50E24DCCA9E"
rx_uuid = "6E400003-B5A3-F393-E0A9-E50E24DCCA9E"
tx_uuid = "6E400002-B5A3-F393-E0A9-E50E24DCCA9E"


x = 0

async def find_device():
    devices = await BleakScanner.discover()

    for device in devices:
        if device.name == "mpy-uart":
            return device

    print("Couldn't find robotic arm")
    return None


async def send_value(pico, motor_index, value):
    if pico and pico.is_connected:
        try:
            await pico.write_gatt_char(tx_uuid, f"{motor_index}:{value}".encode())
            print(f"Sent value {motor_index}:{value}")
        except Exception as e:
            print(f"Failed to send value \n {e}")
    else:
        print(f"Pico not connected but here's the command: {motor_index} {value}")


async def process_frame(hands, frame):
    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = await asyncio.to_thread(
        hands.process, frame_rgb
    )  # Offload processing to a thread

    return results


async def run_handtracking():
    global x
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
                # Draw the hand annotations on the image
                for hand_landmarks in results.multi_hand_landmarks:
                    mp_drawing.draw_landmarks(
                        image=frame,
                        landmark_list=hand_landmarks,
                        connections=mp_hands.HAND_CONNECTIONS,
                        landmark_drawing_spec=mp_drawing_styles.get_default_hand_landmarks_style(),
                        connection_drawing_spec=mp_drawing_styles.get_default_hand_connections_style(),
                    )

                    x = hand_landmarks.landmark[mp_hands.HandLandmark.WRIST].x


            # Display debug info
            frame = cv2.flip(frame, 1)
            cv2.putText(
                frame,                        # Frame to draw on
                f"{x}",                       # Text to display
                (10, 30),                     # Position (x, y)
                cv2.FONT_HERSHEY_SIMPLEX,     # Font
                0.5,                            # Font size (scale)
                (0, 255, 0),                  # Text color (BGR - green here)
                1,                            # Thickness of the text
                cv2.LINE_AA                   # Line type for better rendering
            )

            await asyncio.to_thread(cv2.imshow, "Hand Tracking", frame)
            if cv2.waitKey(1) & 0xFF == ord("q"):
                break
            await asyncio.sleep(0.001)

    cap.release()
    cv2.destroyAllWindows()


async def main():
    pico_device = await find_device()
    async with BleakClient(pico_device) as pico:
        handtracking_task = asyncio.create_task(run_handtracking())

        async def sending_task():
            while not handtracking_task.done():
                await send_value(pico, 1, int((1-x) * 65535))

        await asyncio.gather(
            handtracking_task,
            asyncio.create_task(sending_task())
        )


if __name__ == "__main__":
    asyncio.run(main())
    # asyncio.run(run_handtracking())
