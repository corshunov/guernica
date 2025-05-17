//  X-axis joystick pin: A1
//  Y-axis joystick pin: A0
//  Trim potentiometer pin: A3
//  Button pin: 2

 
#include <Wire.h>
#include <Servo.h>

Servo myservo1;  // create servo object to control a servo
Servo myservo2;  // create servo object to control a servo
Servo myservo3;  // create servo object to control a servo
Servo myservo4;  // create servo object to control a servo
Servo myservo5;  // create servo object to control a servo
Servo myservo6;  // create servo object to control a servo

//include <Adafruit_PWMServoDriver.h>
//Adafruit_PWMServoDriver pwm = Adafruit_PWMServoDriver();

// our servo # counter
uint8_t servonum = 0;

int xval;
int yval;

int expulse;  // x position 
int eypulse;

int uplidpulse;   //upper lid pulse
int lolidpulse;
int altuplidpulse;
int altlolidpulse;

int trimval;

int sensorValue = 0;
int outputValue = 0;
int switchval = 0;  //digital input

bool remote = false;

void setup() {
    Serial.begin(9600);

    pinMode(A0, INPUT);   //Analog input  //Position of the eyes Y
    pinMode(A1, INPUT);   //Analog input  //Position of the eyes X
    pinMode(A3, INPUT);   //Analog input  //Open or close a bit the Eyelids controlled by potentiometer
    pinMode(2, INPUT);    //digital input2 //switch for blinking pulse

    myservo1.attach(3);  // attaches the servo on pin 3 for X EYE position controlled by A1 analog Input
    myservo2.attach(5);  // attaches the servo on pin 5 for Y EYE position controlled by A0 analog Input
    myservo3.attach(7);  // attaches the servo on pin 7 uplidpulse  - left
    myservo4.attach(8);  // attaches the servo on pin 8 lolidpulse  - left
    myservo5.attach(10);  // attaches the servo on pin 10 altuplidpulse - right
    myservo6.attach(12);  // attaches the servo on pin 12 altlolidpulse - right

    myservo1.write(120); // 80 -- 150
    myservo2.write(120);
    myservo3.write(100); // 60 -- 100
    myservo4.write(90); // 90 -- 140
    myservo5.write(70); // 70 -- 120
    myservo6.write(100); // 45 -- 100

    //pwm.begin();
    //pwm.setPWMFreq(60);  // Analog servos run at ~60 Hz updates

    delay(10);
}

// you can use this function if you'd like to set the pulse length in seconds
// e.g. setServoPulse(0, 0.001) is a ~1 millisecond pulse width. its not precise!
void setServoPulse(uint8_t n, double pulse) {
    double pulselength;
    pulselength = 1000000;   // 1,000,000 us per second
    pulselength /= 60;   // 60 Hz
    Serial.print(pulselength);
    Serial.println(" us per period"); 
    pulselength /= 4096;  // 12 bits of resolution
    Serial.print(pulselength);
    Serial.println(" us per bit"); 
    pulse *= 1000000;  // convert to us
    pulse /= pulselength;
    Serial.println(pulse);
}

void loop() {
    if (Serial.available()) {
        String cmd = Serial.readStringUntil('\n');
        cmd.trim();
        long v = cmd.toInt();
        if (cmd == "remote") {
            remote = true;
            Serial.println("Switched to remote control");
            myservo1.detach();
            myservo2.detach();
            myservo3.detach();
            myservo4.detach();
            myservo5.detach();
            myservo6.detach();
        } else if (cmd == "local") {
            remote = false;
            Serial.println("Switched to local control");
            myservo1.attach(3);  // attaches the servo on pin 3 for X EYE position controlled by A1 analog Input
            myservo2.attach(5);  // attaches the servo on pin 5 for Y EYE position controlled by A0 analog Input
            myservo3.attach(7);  // attaches the servo on pin 7 uplidpulse  - left
            myservo4.attach(8);  // attaches the servo on pin 8 lolidpulse  - left
            myservo5.attach(10);  // attaches the servo on pin 10 altuplidpulse - right
            myservo6.attach(12);  // attaches the servo on pin 12 altlolidpulse - right
        } else if (cmd == "blink") {
            myservo3.attach(7);  // attaches the servo on pin 7 uplidpulse  - left
            myservo4.attach(8);  // attaches the servo on pin 8 lolidpulse  - left
            myservo5.attach(10);  // attaches the servo on pin 10 altuplidpulse - right
            myservo6.attach(12);  // attaches the servo on pin 12 altlolidpulse - right

            myservo3.write(45);
            myservo4.write(140);
            myservo5.write(140);
            myservo6.write(45);
            delay(200);
            myservo3.write(120); // 60 -- 100
            myservo4.write(90); // 90 -- 140
            myservo5.write(70); // 70 -- 120
            myservo6.write(100); // 45 -- 100
            delay(100);

            myservo3.detach();
            myservo4.detach();
            myservo5.detach();
            myservo6.detach();
        } else if (v != 0) {
            myservo1.attach(3);
            if (v < 80)
                v = 90;
            if (v > 150)
                v = 140;
            myservo1.write(v);
            delay(100);
            myservo1.detach();
            Serial.print("Setting servo1 ");
            Serial.println(v);
        }
    }

    if (remote)
        return;

    switchval = digitalRead(2);   //DIGITAL INPUT HIGH or LOW
    
    //Position of the eyes X
    xval = analogRead(A1); 
    Serial.print("xval= ");          
    Serial.println(xval);          
    expulse = map(xval, 0,1023, 80, 150);

    //Position of the eyes Y      
    yval = analogRead(A0);
    Serial.print("yval= ");          
    Serial.println(yval);          
    eypulse = map(yval, 0,1023, 90, 140);

    //EYES Y and Y
    myservo1.write(expulse);
    myservo2.write(eypulse);
    //Serial.print("servo2 eyesY = ");
    //Serial.println(eypulse);

    //EYELID Open Close eyelids with potentiometer
    trimval = analogRead(A3);
    trimval = map(trimval, 0, 1023, -30, 30);
    Serial.println(trimval);

    uplidpulse = map(yval, 0, 1023, 45, 125);
    //uplidpulse += trimval;
    //uplidpulse = constrain(uplidpulse, 90, 140);
    lolidpulse = map(yval, 0, 1023, 65, 140);

    altuplidpulse = map(yval, 0, 1023, 140, 55);  //140 low position/eye closed , 55 high position
    //altuplidpulse = 180-uplidpulse;
    //lolidpulse += (trimval/2);
    //lolidpulse = constrain(lolidpulse, 90, 140);      
    //altlolidpulse = 180-lolidpulse;
    altlolidpulse = map(yval, 0, 1023, 125, 45);  //125 low position, 45 high position/eye closed

    //EYELIDS CLOSED
    if (switchval == LOW) {
        myservo3.write(45);
        myservo4.write(140);
        myservo5.write(140);
        myservo6.write(45);
        Serial.print("  switchval HIGH = ");
        Serial.println(uplidpuls
    }
    //EYELIDS OPEN
    else if (switchval == HIGH) {   //connected to ground
        myservo3.write(uplidpulse+trimval);      // attaches the servo on pin 7 uplidpulse  - left
        myservo4.write(lolidpulse-trimval);      // attaches the servo on pin 8 lolidpulse  - left
        myservo5.write(altuplidpulse-trimval);    // attaches the servo on pin 10 altuplidpulse - right
        myservo6.write(altlolidpulse+trimval);   // attaches the servo on pin 12 altlolidpulse - right
        Serial.print("  switchval LOW = ");
        //Serial.println(uplidpulse);
        Serial.println(altlolidpulse);
        //pwm.setPWM(2, 0, uplidpulse);
        //pwm.setPWM(3, 0, lolidpulse);
        //pwm.setPWM(4, 0, altuplidpulse);
        //pwm.setPWM(5, 0, altlolidpulse);
    }

    //Serial.println(trimval);
    delay(5);
}
