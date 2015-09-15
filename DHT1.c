//  How to access GPIO registers from C-code on the Raspberry-Pi
//  Example program
//  15-January-2012
//  Dom and Gert
//


// Access from ARM Running Linux

#define BCM2708_PERI_BASE        0x20000000
#define GPIO_BASE                (BCM2708_PERI_BASE + 0x200000) /* GPIO controller */


#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include <dirent.h>
#include <fcntl.h>
#include <assert.h>
#include <unistd.h>
#include <sys/mman.h>
#include <sys/types.h>
#include <sys/stat.h>
#include <sys/time.h>
#include <bcm2835.h>
#include <unistd.h>
#include <time.h>

#define MAXTIMINGS 100

//#define DEBUG

#define DHT11 11
#define DHT22 22
#define AM2302 22

int readDHT(int type, int pin);
int expectPulse (int level,int pin, int measure_lenght);

int time_array2[100];
int array_counter=0;
int retry_counter=0;

int data[100];

int main(int argc, char **argv)
{
    if (!bcm2835_init())
        return 1;

    if (argc != 3) {
        printf("usage: %s [11|22|2302] GPIOpin#\n", argv[0]);
	    printf("example: %s 2302 4 - Read from an AM2302 connected to GPIO #4\n", argv[0]);
	    return 2;
    }
    int type = 0;
    if (strcmp(argv[1], "11") == 0) type = DHT11;
    if (strcmp(argv[1], "22") == 0) type = DHT22;
    if (strcmp(argv[1], "2302") == 0) type = AM2302;
    if (type == 0) {
	    printf("Select 11, 22, 2302 as type!\n");
	    return 3;
    }
  
    int dhtpin = atoi(argv[2]);

    if (dhtpin <= 0) {
	    printf("Please select a valid GPIO pin #\n");
	    return 3;
    }

    printf("Using pin #%d\n", dhtpin);
    
    while (readDHT(type, dhtpin)!=0 && retry_counter<15)
    {
    	usleep (500000);
        retry_counter++;
        array_counter=0;
    }
    if (retry_counter>=15)
    {
      printf("No valid measurement");
    }
    return 0;
} // main

int readDHT(int type, int pin) {
    bcm2835_gpio_fsel(pin, BCM2835_GPIO_FSEL_INPT);
    bcm2835_gpio_fsel(pin, BCM2835_GPIO_FSEL_OUTP);
    //usleep (1000);
    bcm2835_gpio_fsel(pin, BCM2835_GPIO_FSEL_INPT);
   
    data[0] = data[1] = data[2] = data[3] = data[4] = 0;

    // wait for pin to drop?
    expectPulse (LOW,pin,0);
    expectPulse (HIGH,pin,0);
    for (int i=0; i< 40; i++)
    {
    	expectPulse (LOW,pin,1);
        expectPulse (HIGH,pin,1);
    }
    int average_lenght1=0; //average Lenght of the LOW
    for (int i=0; i< array_counter/2; i++)
    {
      average_lenght1+=time_array2[i*2];
    }
    average_lenght1 = average_lenght1 / (array_counter/2);
    printf("average_lenght1: %d\n", average_lenght1);
    
    for (int i=0; i< array_counter/2; i++)
    {
       if (time_array2[i*2+1]>average_lenght1)
       {
       	 int element_number = i/8;
       	 data[element_number] += (1 << (7-(i-element_number*8)));
       }
    }
    float temp = ((float)(data[2]& 0x7F)*256+data[3])/10;
    if (data[2] & 0x80) //Handle negative temperature
    {
	temp*=-1;    
    }
    float hum = ((float)data[0]*256+data[1])/10;
    
    if (((data[0]+data[1]+data[2]+data[3]) & 0xFF) == data[4] && data[4] != 0x00 && temp >= -40 && temp <= 80 && hum >= 0 && hum <= 100)
    {
      printf("Temp =  %.1f *C, Hum = %.1f \%, Retry = %d\n", temp, hum ,retry_counter);
      return 0;
    }
    else
    {
      return 1;
    }
     bcm2835_gpio_fsel(pin, BCM2835_GPIO_FSEL_INPT);
}    
   
int expectPulse (int level,int pin, int measure_lenght)
{ 
    int counter=0,counter2 = 0;
    while (bcm2835_gpio_lev(pin) != level && counter < 1000) {
        counter++;
        int c=0;
        while (c<200) c++;
    }
    if (counter < 1000)
    {
      if (measure_lenght == 1)
      {
        while (bcm2835_gpio_lev(pin) == level && counter2 < 10000) {
          counter2++;
          int c=0;
          while (c<200) c++;
        }
        if (array_counter<100)
        {
      	  time_array2[array_counter]=counter2;
        }
      }
    }
    
    return counter;
}

