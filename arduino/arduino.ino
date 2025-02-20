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

void processMotorCommand(String value) {
  int colonPos = bt_rx.indexOf(':');
  if (colonPos == -1) {
   Serial.println("Invalid format");
   return;
  }

  String motor = value.substring(0,colonPos);
  int number = value.substring(colonPos + 1).toInt();
  Serial.println(number);

  if (motor == "base"){
    base.write(number);
  }
  if (motor == "bottom"){
    bottom.write(number);
  }
  if (motor == "middle"){
    middle.write(number);
  }
  if (motor == "top"){
    top.write(number);
  }
  if (motor == "hand"){
    hand.write(number);
  }
}

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
  if (btSerial.available()) {
    bt_rx = btSerial.readStringUntil('\n');
    Serial.print("Received:");
    Serial.println(bt_rx);

    processMotorCommand(bt_rx);
  }
}
