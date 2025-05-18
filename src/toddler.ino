// ============
// Toddler eyes
// ============

#define X_PIN           A1
#define Y_PIN           A0
#define EYELID_PIN      A3
#define BLINK_PIN        2

#define X_MIN           80
#define X_MAX          150
#define X_DELTA         10

#define Y_MIN           90
#define Y_MAX          140

#define UP_LID_L_CL     45
#define LO_LID_L_CL    140
#define UP_LID_R_CL    140
#define LO_LID_R_CL     45

#define UP_LID_L_OP    120 // 60 -- 100
#define LO_LID_L_OP     90 // 90 -- 140
#define UP_LID_R_OP     70 // 70 -- 120
#define LO_LID_R_OP    100 // 45 -- 100

#define X_INIT         120
#define Y_INIT         120
#define UP_LID_L_INIT  100 // 60 -- 100
#define LO_LID_L_INIT   90 // 90 -- 140
#define UP_LID_R_INIT   70 // 70 -- 120
#define LO_LID_R_INIT  100 // 45 -- 100

#include <Wire.h>
#include <Servo.h>

Servo s1; // x 
Servo s2; // y
Servo s3; // upper eyelid left
Servo s4; // lower eyelid left
Servo s5; // upper eyelid right
Servo s6; // lower eyelid right

bool remote = true;

int x_val, y_val, eyelid_val;
int x, y, eyelid, blink;
int upper_eyelid_left, lower_eyelid_left;
int upper_eyelid_right, lower_eyelid_right;

void attachAll() {
    s1.attach(3);
    s2.attach(5);
    s3.attach(7);
    s4.attach(8);
    s5.attach(10);
    s6.attach(12);
}

void detachAll() {
    s1.detach();
    s2.detach();
    s3.detach();
    s4.detach();
    s5.detach();
    s6.detach();
}

void blink() {
    s3.attach(7);
    s4.attach(8);
    s5.attach(10);
    s6.attach(12);

    s3.write(UP_LID_L_CL);
    s4.write(LO_LID_L_CL);
    s5.write(UP_LID_R_CL);
    s6.write(LO_LID_R_CL);
    delay(200);

    s3.write(UP_LID_L_OP); 
    s4.write(LO_LID_L_OP);  
    s5.write(UP_LID_R_OP);  
    s6.write(LO_LID_R_OP); 
    delay(100);

    s3.detach();
    s4.detach();
    s5.detach();
    s6.detach();
}

int safeClamp(int v, int v_min, int v_max, int delta) {
    if (v < v_min) {
        v = v_min + delta;
    } else if (v > v_max) {
        v = v_max - delta
    }
    return v
}

void setX(v) {
    s1.attach(3);
    s1.write(v);
    delay(100);
    s1.detach();
}

void local_control() {
    x_val = analogRead(X_PIN); 
    Serial.print("x_val= ");          
    Serial.println(x_val);          
    x = map(x_val, 0, 1023, 80, 150);

    y_val = analogRead(Y_PIN);
    Serial.print("y_val= ");          
    Serial.println(y_val);          
    y = map(y_val, 0, 1023, 90, 140);

    s1.write(x);
    s2.write(y);

    eyelid_val = analogRead(EYELID_PIN);
    Serial.print("eyelid_val= ");          
    Serial.println(eyelid_val);
    eyelid = map(eyelid_val, 0, 1023, -30, 30);

    upper_eyelid_left = map(y_val, 0, 1023, 45, 125);
    lower_eyelid_left = map(y_val, 0, 1023, 65, 140);

    upper_eyelid_right = map(y_val, 0, 1023, 140, 55);
    lower_eyelid_right = map(y_val, 0, 1023, 125, 45);

    blink = digitalRead(BLINK_PIN);
    if (blink == LOW) { // closed
        s3.write(45);
        s4.write(140);
        s5.write(140);
        s6.write(45);
    } else { // opened
        s3.write(upper_eyelid_left  + eyelid);
        s4.write(lower_eyelid_left  - eyelid);
        s5.write(upper_eyelid_right - eyelid);
        s6.write(lower_eyelid_right + eyelid);
    }
}

void setup() {
    Serial.begin(9600);

    pinMode(X_PIN,      INPUT);
    pinMode(Y_PIN,      INPUT);
    pinMode(EYELID_PIN, INPUT);
    pinMode(BLINK_PIN,  INPUT);

    attachAll()

    s1.write(X_INIT);
    s2.write(Y_INIT);
    s3.write(UP_LID_L_INIT); 
    s4.write(LO_LID_L_INIT);  
    s5.write(UP_LID_R_INIT);  
    s6.write(LO_LID_R_INIT); 
}

void loop() {
    if (Serial.available()) {
        String cmd = Serial.readStringUntil('\n');
        cmd.trim();

        long v = cmd.toInt();

        if (cmd == "remote") {
            remote = true;
            detachAll()
            Serial.println("Switched to remote control");
        } else if (cmd == "local") {
            remote = false;
            attachAll()
            Serial.println("Switched to local control");
        } else if (cmd == "blink") {
            blink();
        } else if (v != 0) {
            v = safeClamp(v, X_MIN, X_MAX, X_DELTA);
            setX(v);
            //Serial.print("Setting X to ");
            //Serial.println(v);
        }
    }

    if (!remote) {
        local_control();
    }

    delay(5);
}
