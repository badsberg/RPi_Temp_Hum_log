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

int time_array[100], level_array[100];
int array_counter=0;
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
    readDHT(type, dhtpin);
    return 0;
} // main

int readDHT(int type, int pin) {
    bcm2835_gpio_fsel(pin, BCM2835_GPIO_FSEL_INPT);
     // Set GPIO pin to output
    bcm2835_gpio_fsel(pin, BCM2835_GPIO_FSEL_OUTP);
    //usleep(100);
    
    //cm2835_gpio_write(pin, LOW);
    //usleep(1000); //2 ms
    //bcm2835_gpio_write(pin, HIGH);
    //usleep(1); //40 us

    bcm2835_gpio_fsel(pin, BCM2835_GPIO_FSEL_INPT);
    //usleep(100);

    data[0] = data[1] = data[2] = data[3] = data[4] = 0;

    // wait for pin to drop?
    expectPulse (LOW,pin,0);
    expectPulse (HIGH,pin,0);
    for (int i=0; i< 42; i++)
    {
    	expectPulse (LOW,pin,1);
        expectPulse (HIGH,pin,1);
    }
    for (int i=0; i< array_counter/2; i++)
    {
       printf ("expectPulse: array_counter %d / %d, Level %d / %d, duration %d / %d ", i*2,i*2+1,level_array[i*2],level_array[i*2+1],time_array[i*2],time_array[i*2+1]);
       if (time_array[i*2]>time_array[i*2+1])
       {
         printf ("Compare: %d - %d. Bit=1\n",i*2,i*2+1);
       }
       else
       {
         printf ("Compare: %d - %d. Bit=0\n",i*2,i*2+1);
       }   
    }
}    
   
int expectPulse (int level,int pin, int measure_lenght)
{ 
   struct timespec tim;
   tim.tv_sec = 0;
   tim.tv_nsec = 1;

   
 // wait for pin to drop?
    int counter = 0;
    while (bcm2835_gpio_lev(pin) != level && counter < 1000) {
        counter++;
        //nanosleep(&tim,NULL);
    }
    if (measure_lenght == 1 && counter>=1000)
    {
      counter = 0;
      while (bcm2835_gpio_lev(pin) == level && counter < 10000) {
        counter++;
        //nanosleep(&tim,NULL);
      }
    }
    else
    {
       counter = 100000;
    }

    if (array_counter<100)
      {
        time_array[array_counter]=counter;
        level_array[array_counter++]=level;
      }
    
    
    return counter;
}

