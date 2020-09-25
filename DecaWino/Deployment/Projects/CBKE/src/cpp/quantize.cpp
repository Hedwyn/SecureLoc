#include "quantize.h"
//#include <stdio.h>


float compute_mean(float *array, int length) {
    int i;
    float mean = 0;
    for (i = 0; i < length; i ++) {
        mean += array[i];
    }
    if (length > 0) {
        mean = mean /(float) length;
    }
    return(mean);
}

float min(float a, float b) {
    return (a < b)?a:b;
}

float compute_std(float *array, int length) {
    int i;
    float mean = compute_mean(array, length), std = 0;
    for (i = 0; i < length; i++) {
        std += pow(array[i] - mean, 2);
    }
    if (length > 0) {
        std = sqrt(std / length);
    }
    return(std);
}

void center_array(float *array, int length) {
    int i;
    float mean = compute_mean(array, length);
    for (i = 0; i < length; i++) {      
        array[i] = array[i] - mean;
    }
}

void substract_moving_average(float *array, int length, int window_size) {
    int i,j;
    float moving_average, temp;
    for (i = 0; i < window_size; i++) {
        moving_average += array[length - 1 - i];
    }
    moving_average /= window_size;
    for (i = length - 1; i >= window_size; i--)  {
        temp = array[i];
        array[i] -= moving_average;
        moving_average += (array[i - window_size] - temp) / window_size;
    }
    for (i = window_size - 1; i >= 0; i --) {
        temp = array[i];
        array[i] -= moving_average;
        moving_average *= (i + 1);
        moving_average -= temp;
        moving_average /= i;       
    }
}

void median_filter(float *array, float *filtered_array, int array_length) {
    int i = 0, j = 0, length;
    while (i < array_length) {
        length = min(array_length - i , MEDIAN_WINDOW_LENGTH);
        filtered_array[j++] = median(&array[i], length);
        i += MEDIAN_WINDOW_LENGTH;
    }
}

void swap(float *a, float *b) {
    float t = *a;
    *a = *b;
    *b = t;
}

float median(float *array, int length) {
    int i, j;
    float buffer[MEDIAN_WINDOW_LENGTH];
    float median;
    /* copying values in buffer */
    for (i = 0; i < length; i++) {
        buffer[i] = array[i];
    }
    /* sorting */
    for (i = 0; i < length - 1 ; i++) {
        for (j = 0; j < length - i - 1; j++) {
            if (buffer[j] > buffer[j + 1]) {
                swap(&buffer[j], &buffer[j + 1]);
            }
        }                  
    }
    /* calculating median */
    if (length == 0) {
        median = 0;
    }
    else if (length % 2 == 0) {
        median = (buffer[length / 2] + buffer[length / 2 - 1]) / 2;
    }
    else {
        median = buffer[length / 2];
    }
    return(median);

}    
 
int quantize_chunk(float *array, int length, char *bit_array) {
    float std, threshold;
    float processed_array[KEY_CHUNK_LENGTH];
    int length_after_filtering,i, j = 0;
    median_filter(array, processed_array, length);
    array = processed_array;
    length_after_filtering = ((length - 1) / MEDIAN_WINDOW_LENGTH) + 1;
    center_array(array, length_after_filtering);
    // substract_moving_average(array, length_after_filtering, 4);
    std = compute_std(array, length_after_filtering);  
    threshold = GAUSSIAN_MID_RATIO * std;
    /* quantizing 2 bits per sample */
    for (i = 0; i < length_after_filtering; i++) {
        if (array[i] > 0) {
            bit_array[2 * i] = '1';
            
            if (array[i] > threshold) {
                bit_array[2 *  i + 1] = '1';
            }
            else {
                bit_array[2 *  i + 1] = '0';

            }
        }
        else {
            bit_array[2 * i] = '0';
            if (-array[i] > threshold) {
                bit_array[2 *  i + 1] = '0';
            }
            else {
                bit_array[2 *  i + 1] = '1';
            }
        }
    }
    for (i = 0; i < 2 * length_after_filtering; i++) {
        Serial.print(bit_array[i]);
    }
    //Serial.print("|");  
    return(2 * length_after_filtering);
}

void get_pulse_idx_values(float *values, float *pulses, int pulse_idx, int pulse_length, int nb_pulses) {
    int i;
    for (i = 0; i < nb_pulses; i++) {
        values[i] = pulses[pulse_idx + pulse_length * i];
    }
}

float check_bit_balance(char *key, int  length) {
    int i,j, one_counter = 0;
    for (i = 0; i < length; i++) {
        Serial.print(key[i]);
        if (key[i] == '1') {
            one_counter++;
        }  
    }
    Serial.println();
    Serial.print("1 counter:");
    Serial.println(one_counter);
    return((float) one_counter / (float) length);
}

/** Test Module for the functions on this module. 
 * Uncomment to test the features. Also uncomment #include <stdio.h> in Multilateration.h.
 * Compile with 'g++ Multilateration.cpp -o Test -I ../header' */

//  int main() {
//      float test_array[] = {3.73, 4.51,  9.62, 8.4, 1.02, 5.3};
//      float test_array2[] = {1.2, -0.6, 2, 3, -5, 4.5,8.9,-5,-2,1,13,4.1};
//      float output[10];
//      printf("Median:%f\n", median(test_array, 4));
//      median_filter(test_array2, output, 12);
//      for (int i = 0; i < 4; i++) {
//          printf("%f;", output[i]);
//      }
//      center_array(test_array2, 12);
//      printf("\n");
//      for (int i = 0; i < 12; i++) {
//          printf("%f;", test_array2[i]);
//      }     
//      return(0);
//  }