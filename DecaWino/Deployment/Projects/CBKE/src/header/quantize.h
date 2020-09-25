#ifndef QUANTIZE_H
#define QUANTIZE_H

#include <math.h>
#include "CBKE.h"
#include <SPI.h>
#define GAUSSIAN_MID_RATIO 0.667
#define MEDIAN_WINDOW_LENGTH SAMPLES_PER_BIT


typedef struct Linked_list Linked_list;
struct Linked_list{
    float value;
    Linked_list *next;
};

float compute_mean(float *array, int length);
float compute_std(float *array, int length);
void center_array(float *array, int length);
int quantize_chunk(float *array, int length, char *bit_array);
float check_bit_balance(char *key, int  length);
float median(float *array, int length);
void substract_moving_average(float *array, int length, int window_size);
float min(float a, float b);

#endif