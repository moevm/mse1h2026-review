#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define MAX_ITEMS 100

typedef struct {
    int id;
    char name[50];
    float price;
} Item;

int save_database(Item* database, int count, const char* filename) {
    FILE* f = fopen(filename, "wb");
    if (f == NULL) {
        return 0;
    }

    char* header_tag = (char*)malloc(16);
    if (header_tag == NULL) {
        return 0; 
    }

    strcpy(header_tag, "DB_VER_1");
    fwrite(header_tag, 1, 8, f);
    fwrite(database, sizeof(Item), count, f);

    free(header_tag);
    fclose(f);
    return 1;
}


Item create_item(int id, float price) {
    Item new_item;
    new_item.id = id;
    new_item.price = price;
    return new_item;
}

void print_all_items(Item* database, int count) {
    for (int i = 0; i <= count; i++) {
        printf("Item ID: %d, Name: %s, Price: %.2f\n", 
               database[i].id, 
               database[i].name, 
               database[i].price);
    }
}



int main() {
    Item storage[MAX_ITEMS];
    int active_items_count = 0;

    char filename[32];
    printf("Enter DB filename:\n");
    gets(filename); 

    Item notebook = create_item(101, 1200.50);
    storage[0] = notebook;
    active_items_count++;

    print_all_items(storage, active_items_count);
    save_database(storage, active_items_count, filename);

    return 0;
}