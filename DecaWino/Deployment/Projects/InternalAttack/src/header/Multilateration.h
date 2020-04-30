#ifndef MULTILATERATION_H
#define MULTILATERATION_H

#include <math.h>
#include <stdio.h>

#define SQUARE(...) pow (__VA_ARGS__, 2)
#define MAX_SOLUTIONS 20
#define RESOLUTION 0.01/**<Lowest measurable distance, in m */

/** @brief represents a position with its coordinates */
typedef struct Position{
  float x;/**<x coordinate */
  float y;/**<y coordinate */
}Position;

float compute_distance(Position *a, Position *b);
float compute_mse(Position *p, Position *anchors, float *distances, int nb_anchors);
void multilateration(Position *position, Position* anchors, float *distances, int nb_anchors);
void trilateration_2D(Position *solution, Position *anchor_A, Position *anchor_B, float distance_A, float distance_B);



#endif