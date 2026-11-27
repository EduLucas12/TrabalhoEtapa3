/**
 * @file bubble_sort.c
 * @author [Seu nome aqui]
 * @date [Data de criação aqui]
 * @brief Implementação do algoritmo Bubble Sort em C.
 */

#include <stdio.h>

/**
 * @brief Função que ordena um array utilizando o algoritmo Bubble Sort.
 *
 * @param array   Ponteiro para o array a ser ordenado.
 * @param tamanho Tamanho do array a ser ordenado.
 */
void bubble_sort(int *array, int tamanho) {
    int i, j;
    int troca;

    for (i = 0; i < tamanho - 1; i++) {
        troca = 0;

        for (j = 0; j < tamanho - i - 1; j++) {
            if (array[j] > array[j + 1]) {
                int temporario = array[j];
                array[j] = array[j + 1];
                array[j + 1] = temporario;
                troca = 1;
            }
        }

        if (!troca) {
            break;
        }
    }
}

/**
 * @brief Função que imprime o conteúdo de um array.
 *
 * @param array   Ponteiro para o array a ser impresso.
 * @param tamanho Tamanho do array a ser impresso.
 */
void imprime_array(int *array, int tamanho) {
    int i;

    printf("Array ordenado: ");
    for (i = 0; i < tamanho; i++) {
        printf("%d ", array[i]);
    }
    printf("\n");
}

int main() {
    int array[] = {5, 2, 8, 1, 9};
    int tamanho = sizeof(array) / sizeof(array[0]);

    printf("Array original: ");
    for (int i = 0; i < tamanho; i++) {
        printf("%d ", array[i]);
    }
    printf("\n");

    bubble_sort(array, tamanho);

    imprime_array(array, tamanho);

    return 0;
}
