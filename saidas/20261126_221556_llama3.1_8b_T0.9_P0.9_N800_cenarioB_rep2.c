#include <stdio.h>

/**
 * Função de ordenação Bubble Sort.
 *
 * @param array   Ponteiro para o array a ser ordenado.
 * @param tamanho Tamanho do array.
 */
void bubbleSort(int *array, int tamanho) {
    int i, j;
    int troca;

    // Iterações necessárias para garantir que o array está ordenado
    for (i = 0; i < tamanho - 1; i++) {
        // Suponha que o array está ordenado até a posição i
        troca = 0;

        // Compare cada par de elementos e troque-os se necessário
        for (j = 0; j < tamanho - i - 1; j++) {
            if (array[j] > array[j + 1]) {
                // Troque os elementos
                int temp = array[j];
                array[j] = array[j + 1];
                array[j + 1] = temp;
                troca = 1;
            }
        }

        // Se nenhuma troca foi feita na iteração atual, o array já está ordenado
        if (troca == 0) {
            break;
        }
    }
}

/**
 * Exemplo de uso da função bubbleSort.
 */
int main() {
    int array[] = {64, 34, 25, 12, 22, 11, 90};
    int tamanho = sizeof(array) / sizeof(array[0]);

    printf("Array antes da ordenação: ");
    for (int i = 0; i < tamanho; i++) {
        printf("%d ", array[i]);
    }
    printf("\n");

    bubbleSort(array, tamanho);

    printf("Array após a ordenação: ");
    for (int i = 0; i < tamanho; i++) {
        printf("%d ", array[i]);
    }
    printf("\n");

    return 0;
}
