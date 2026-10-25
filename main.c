#define _CRT_SECURE_NO_WARNINGS
#pragma execution_character_set("utf-8")
#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>
#include <omp.h>

typedef struct { int id; float* data; int dim; } VectorItem;

float cosine_similarity(float* v1, float* v2, int dim) {
    float dot_product = 0.0f, norm_v1 = 0.0f, norm_v2 = 0.0f;
    for (int i = 0; i < dim; i++) {
        dot_product += v1[i] * v2[i];
        norm_v1 += v1[i] * v1[i];
        norm_v2 += v2[i] * v2[i];
    }
    if (norm_v1 == 0.0f || norm_v2 == 0.0f) return 0.0f;
    return (float)(dot_product / (sqrt(norm_v1) * sqrt(norm_v2)));
}

int main() {
    system("chcp 65001 > nul");
    int dim = 1024;

    FILE* file = fopen("vectors.csv", "r");
    if (file == NULL) return 1;

    int max_items = 2000000; // 支持200万级别数据
    VectorItem* db = (VectorItem*)malloc(max_items * sizeof(VectorItem));
    int db_size = 0;
    char line[16384];

    while (fgets(line, sizeof(line), file) && db_size < max_items) {
        if (strlen(line) < 3) continue;
        char* token = strtok(line, ",");
        if (token == NULL) continue;
        db[db_size].id = atoi(token);
        db[db_size].dim = dim;
        db[db_size].data = (float*)malloc(dim * sizeof(float));
        for (int i = 0; i < dim; i++) {
            token = strtok(NULL, ",");
            if (token != NULL) db[db_size].data[i] = (float)atof(token);
        }
        db_size++;
    }
    fclose(file);

    FILE* qfile = fopen("query.csv", "r");
    if (qfile == NULL) return 1;

    float* query = (float*)malloc(dim * sizeof(float));
    char q_line[16384];
    if (fgets(q_line, sizeof(q_line), qfile)) {
        char* token = strtok(q_line, ",");
        for (int i = 0; i < dim; i++) {
            token = strtok(NULL, ",");
            if (token != NULL) query[i] = (float)atof(token);
        }
    }
    fclose(qfile);

    int K = 3;
    float* max_sims = (float*)malloc(K * sizeof(float));
    int* best_ids = (int*)malloc(K * sizeof(int));
    for (int k = 0; k < K; k++) { max_sims[k] = -1.0f; best_ids[k] = -1; }

    double start_time = omp_get_wtime();
    int i;
#pragma omp parallel for
    for (i = 0; i < db_size; i++) {
        float sim = cosine_similarity(query, db[i].data, dim);
        if (sim > max_sims[K - 1]) {
#pragma omp critical
            {
                if (sim > max_sims[K - 1]) {
                    max_sims[K - 1] = sim; best_ids[K - 1] = db[i].id;
                    for (int k = K - 1; k > 0; k--) {
                        if (max_sims[k] > max_sims[k - 1]) {
                            float temp_sim = max_sims[k]; max_sims[k] = max_sims[k - 1]; max_sims[k - 1] = temp_sim;
                            int temp_id = best_ids[k]; best_ids[k] = best_ids[k - 1]; best_ids[k - 1] = temp_id;
                        }
                    }
                }
            }
        }
    }
    double end_time = omp_get_wtime();

    for (int k = 0; k < K; k++) if (best_ids[k] != -1) printf("%d ", best_ids[k]);
    fprintf(stderr, "\n======================================================\n");
    fprintf(stderr, "[Performance] Parallel search %d vectors took: %.6f seconds\n", db_size, end_time - start_time);
    fprintf(stderr, "======================================================\n");

    for (int i = 0; i < db_size; i++) free(db[i].data);
    free(db); free(query); free(max_sims); free(best_ids);
    return 0;
}