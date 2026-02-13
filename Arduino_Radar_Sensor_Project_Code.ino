#include <Servo.h>
#include <NewPing.h>

#define TRIG_PIN 11
#define ECHO_PIN 12
#define SERVO_PIN 9
#define MAX_DISTANCE 200  // Maximum distance in cm

Servo myServo;
NewPing sonar(TRIG_PIN, ECHO_PIN, MAX_DISTANCE);

void setup() {
  Serial.begin(9600);
  myServo.attach(SERVO_PIN);
}

void loop() {
  // Sweep from 15° to 165°
  for (int angle = 0; angle <= 180
  ; angle++) {
    myServo.write(angle);
    delay(15);
    int distance = sonar.ping_cm();
    Serial.print(angle);
    Serial.print(",");
    Serial.print(distance);
    Serial.print(".");
  }
  // Sweep back from 165° to 15°
  for (int angle = 180; angle >= 0; angle--) {
    myServo.write(angle);
    delay(15);
    int distance = sonar.ping_cm();
    Serial.print(angle);
    Serial.print(",");
    Serial.print(distance);
    Serial.print(".");
  }
}