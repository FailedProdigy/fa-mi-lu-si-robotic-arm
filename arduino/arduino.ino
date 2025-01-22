#include <SoftwareSerial.h>
#include <Servo.h>

SoftwareSerial btSerial(7, 8); // RX, TX PIN

Servo base;
Servo bottom;
Servo middle;
Servo top;
Servo hand;

String bt_rx;
int ledpin = 13;

void setup() {
  base.attach(10);
  bottom.attach(9);
  middle.attach(6);
  top.attach(5);
  hand.attach(3);

  Serial.begin(9600);
  pinMode(ledpin, OUTPUT);
  btSerial.begin(9600);
}

void loop() {
  
  // base.write(150);
  // bottom.write(150);
  // middle.write(150);
  // top.write(150);
  // hand.write(150);

  
  // if (Serial.available() > 0) {
  //   String value = Serial.readStringUntil('\n');
  //   int num = value.toInt();
  //   base.write(num);
  // }
  if (btSerial.available()) {
    bt_rx = btSerial.readStringUntil('\n');
    // bt_rx = btSerial.readString();
    Serial.print("Received:");
    Serial.println(bt_rx);
    if (bt_rx == "led_on") {
      digitalWrite(ledpin, HIGH);
      // btSerial.println("LED turned on");
    }
    if (bt_rx == "led_off") {
      digitalWrite(ledpin, LOW);
      // btSerial.println("LED turned off");
    }
  }
}
