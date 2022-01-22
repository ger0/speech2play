#include <LCD_I2C.h>

#define NOW_PLAYING "$INPUT:NOW_PLAYING"
#define SPEAK_NOW   "$INPUT:SPEAK_NOW"
#define CLEAR       "$INPUT:CLEAR"

LCD_I2C lcd(0x27, 16, 2);

String input;
bool   isScrolling = false;

void setup() {
  lcd.begin();
  lcd.backlight();
  lcd.clear();
  Serial.begin(9600);
  lcd.print("booting up...");
}

void loop() {
  if (Serial.available()) {
   // reset pos
   lcd.setCursor(0, 0);
   input = Serial.readStringUntil('\n');
   
   if (input == NOW_PLAYING) {
    lcd.setCursor(1, 1);
    lcd.backlight();
    isScrolling = true;
    lcd.print("Now playing...");
    
   } else if (input == SPEAK_NOW) {
    lcd.clear();
    lcd.setCursor(2, 0);
    lcd.backlight();
    isScrolling = false;
    lcd.print("Speak now...");
    
   } else if (input == CLEAR) {
    lcd.clear();
    lcd.noBacklight();
    
   } else {
     lcd.print(input);
   }
  }
  if (isScrolling) {
    lcd.scrollDisplayLeft();
    delay(500);
  } else {
    delay(175);
  }
}
