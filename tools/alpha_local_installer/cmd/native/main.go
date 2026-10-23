package main

/*
#include <stdlib.h>
*/
import "C"
import (
	"errors"
	"flexygram.local/installer/internal/delivery"
	"os"
)

//export DecryptDelivery
func DecryptDelivery(cipherFD C.int, identityFD C.int, output *C.char) C.int {
	cipher := os.NewFile(uintptr(cipherFD), "encrypted-delivery")
	identity := os.NewFile(uintptr(identityFD), "selected-identity")
	if cipher == nil || identity == nil {
		return 3
	}
	defer cipher.Close()
	defer identity.Close()
	if err := delivery.Decrypt(cipher, identity, C.GoString(output)); err != nil {
		if errors.Is(err, delivery.ErrIdentity) {
			return 1
		}
		if errors.Is(err, delivery.ErrIntegrity) {
			return 2
		}
		return 3
	}
	return 0
}

func main() {}
