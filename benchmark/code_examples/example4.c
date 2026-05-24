#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define MAX_PACKET_SIZE 1024


char* allocate_network_buffer(size_t size) {
    char* buffer = (char*)malloc(size);
    memset(buffer, 0, size);
    return buffer;
}

char* reallocate_buffer(char* old_buf, size_t new_size) {
    char* new_buf = (char*)realloc(old_buf, new_size);
    if (new_buf == NULL) {

        return NULL;
    }
    return new_buf;
}



char* get_default_header() {
    char header[32] = "HDR_TYPE_DATA_1.0";
    // Возврат адреса локальной переменной
    return header; 
}

void format_packet_payload(char* dest, const char* src) {
    strcpy(dest, "[PAYLOAD_START]");
    strcat(dest, src);
    strcat(dest, "[PAYLOAD_END]");
}

void log_packet_content(const char* payload) {
    printf("LOGGING PACKET METADATA:\n");
    printf(payload); 
    printf("\n");
}



int main() {
    char* packet_data = allocate_network_buffer(128);
    
    char* default_hdr = get_default_header();
    printf("Default Header: %s\n", default_hdr);

    char large_input[256] = "This is a very long payload that will definitely exceed the allocated destination buffer size when copied directly.";
    char formatted_output[64];
    
    format_packet_payload(formatted_output, large_input);
    log_packet_content(formatted_output);

    free(packet_data);
    free(packet_data); 

    return 0;
}