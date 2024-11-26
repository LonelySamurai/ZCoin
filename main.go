package main

import (
	"encoding/json"
	"fmt"
	"log"
	"net/http"

	"github.com/gorilla/mux"
)

var BlockChain *Blockchain

// /////////////
func main() {

	fmt.Println("\033[1;31mZCoin Inc. (2023)\n\033[0m")
	BlockChain = NewBlockchain()

	r := mux.NewRouter()

	r.HandleFunc("/", getBlockchain).Methods("GET")
	r.HandleFunc("/", writeBlock).Methods("POST")
	r.HandleFunc("/new", newNFT).Methods("POST")

	go func() {

		for _, block := range BlockChain.blocks {
			fmt.Printf("Previous Hash: %x\n", block.PrevHash)
			bytes, _ := json.MarshalIndent(block.Data, "", " ")
			fmt.Printf("Data: %v\n", string(bytes))
			fmt.Printf("Hash: %x\n", block.Hash)
			fmt.Println()
		}
	}()

	log.Println("Listening on port 3000")
	log.Fatal(http.ListenAndServe(":3000", r))

}
