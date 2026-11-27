#include <stdio.h>

/**
 * Função para ordenar uma lista de elementos usando Bubble Sort.
 *
 * @param arr   Ponteiro para o início da lista a ser ordenada.
 * @param n     Tamanho da lista.
 */
void bubbleSort(int* arr, int n) {
    int i, j;
    int troca;

    // Iterações para ordenar a lista
    for (i = 0; i < n - 1; i++) {
        // Flag para verificar se ocorreu troca em uma iteração
        troca = 0;

        // Iterações para comparar cada par de elementos consecutivos
        for (j = 0; j < n - i - 1; j++) {
            // Se o elemento atual for maior que o elemento seguinte, troque-os
            if (arr[j] > arr[j + 1]) {
                // Troca os elementos
                int temp = arr[j];
                arr[j] = arr[j + 1];
                arr[j + 1] = temp;

                // Seta a flag para 1, pois ocorreu troca
                troca = 1;
            }
        }

        // Se não ocorreu troca em uma iteração, a lista já está ordenada
        if (!troca) {
            break;
        }
    }
}

int main() {
    int arr[] = {64, 34, 25, 12, 22, 11, 90};
    int n = sizeof(arr) / sizeof(arr[0]);

    printf("Lista original: ");
    for (int i = 0; i < n; i++) {
        printf("%d ", arr[i]);
    }
    printf("\n");

    bubbleSort(arr, n);

    printf("Lista ordenada: ");
    for (int i = 0; i < n; i++) {
        printf("%d ", arr[i]);
    }
    printf("\n");

    return 0;
}
