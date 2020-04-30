#include "Multilateration.h"

float compute_distance(Position *a, Position *b) {
    float distance, distance_squared = SQUARE(a->x - b->x) + SQUARE(a->y - b->y);
    distance = (distance_squared > 0)?sqrt(distance_squared):0;
    return(distance);
}

float compute_mse(Position *p, Position *anchors, float *distances, int nb_anchors) {
    int idx;
    float distance_to_anchor; /* distance between the position and the processed anchor */
    float mse = 0; /* mean-squared error for the given position */
    for (idx = 0; idx < nb_anchors; idx++) {
        distance_to_anchor = compute_distance(p, anchors++ );
        mse += SQUARE(distances[idx] - distance_to_anchor);
    }
    return(mse);

}

void trilateration_2D(Position *solutions, Position *anchor_A, Position *anchor_B, float distance_A, float distance_B) {
    /* Applying Pythagora's theorem */
    float base; /* distance between the two anchors */
    float X, Y; /* relative coordinates in the (A,B) system */
    float mse1, mse2; /* mean-squared error of the two solutions */
    Position x_vector, y_vector;
    Position solution1, solution2; /* two solutions are possible */

    /* computing relative coordinates */
    base = compute_distance(anchor_A, anchor_B);
    X = ( SQUARE(distance_A) - SQUARE(distance_B) + SQUARE(base) ) / (2 * base);
    Y = SQUARE(distance_A) - SQUARE(X);
    /* Y squared can be negative because of the noise, in that case simply zeroing Y */
    Y = (Y > 0)?sqrt(Y):0;

    /* computing absolute coordinates -> coordinates change */

    /* calculating base vectors of the cartesian orthonormal system (A,B) */
    x_vector.x = (anchor_B ->x - anchor_A->x) / base;
    x_vector.y = (anchor_B ->y - anchor_A->y) / base;
    y_vector.x = -(x_vector.y);
    y_vector.y = x_vector.x;
    /* computing P = (x,y) as P = X * x_vector + Y * y_vector. The second solution is the symmetric of the first one about x axis*/
    solution1.x = anchor_A->x + (x_vector.x * X) + (y_vector.x * Y);
    solution1.y = anchor_A->y + (x_vector.y * X) + (y_vector.y * Y);

    solution2.x = anchor_A->x + (x_vector.x * X) - (y_vector.x * Y);
    solution2.y = anchor_A->y + (x_vector.y * X) - (y_vector.y * Y);
    /* writing the two solutions */
    solutions->x = solution1.x;
    (solutions++)->y = solution1.y;
    //printf("Relative coord. %f %f", x, y);

    solutions->x = solution2.x;
    solutions->y = solution2.y;
}

void multilateration(Position *position, Position* anchors, float *distances, int nb_anchors) {
    int i,j,k, solution_idx = 0;
    Position solutions[MAX_SOLUTIONS]; /** 2 solutions per anchor pair + factorial(nb_anchors) / 2 permutations  */
    Position *iterator = solutions;
    float mse_inv[MAX_SOLUTIONS]; /* inverse of MSE -> indicates how likely is the solution */
    float sum_mse_inv = 0;
    for (i = 0; i < nb_anchors - 1; i++) {
        for (j= i + 1 ; j < nb_anchors; j++) {
            trilateration_2D(iterator, (anchors + i), (anchors + j), distances[i], distances[j]);

            /* 1st solution */
            mse_inv[solution_idx++] = 1 / (compute_mse(iterator++, anchors, distances, nb_anchors) + RESOLUTION);

            /* second solution */
            mse_inv[solution_idx++] = 1 / (compute_mse(iterator++, anchors, distances, nb_anchors) + RESOLUTION);      

            sum_mse_inv += mse_inv[solution_idx - 1 ] + mse_inv[solution_idx - 2 ];      
        }
    }

    /* weighting solutions */
    position->x = 0;
    position->y = 0;
    for (k = 0; k < solution_idx; k++) {
        position->x += (mse_inv[k] / sum_mse_inv) * solutions[k].x; 
        position->y += (mse_inv[k] / sum_mse_inv) * solutions[k].y; 
    }
}


/** Test Module for the functions on this module. 
 * Uncomment to test the features. Also uncomment #include <stdio.h> in Multilateration.h.
 * Compile with 'g++ Multilateration.cpp -o Test -I ../header' */

// int main() {
//     /* Testing compute distance */

//     Position *a, *b, *c, *d; /**< references to anchors */
//     Position tag; /**< localized device */
//     Position solutions[8];
//     Position anchors[4] = { {0, 0}, {0, 3}, {3, 3}, {3, 0}};
//     Position middle = {1.5, 1.5};
//     float distances[4] = {2.2,2.3,2.0,2.1};
//     a = &anchors[0];
//     b = &anchors[1];
//     c = &anchors[2];
//     d = &anchors[3];
//     printf("distance AC: %f\n", compute_distance(a, c));
//     printf("distance A-middle: %f\n", compute_distance(d, &middle));

//     /* testing mse */
//     printf("MSE for middle position: %f\n", compute_mse(&middle, anchors, distances, 4) );
    
//     /* testing trilateration */
//     trilateration_2D(solutions, a, b, distances[0], distances[1]);
//     printf("Calculated tag coordinates, 1st solution: (%f, %f)\n", solutions[0].x, solutions[0].y);
//     printf("Calculated tag coordinates, 2nd solution: (%f, %f)\n", solutions[1].x, solutions[1].y);

//     /* testing multilateration */
//     multilateration(&tag, anchors, distances, 4);
//     printf("Final calculated tag coordinates: (%f, %f)\n", tag.x, tag.y);
// }