package main

import (
	"crypto/md5"
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"fmt"
	"io"
	"log"
	"net/http"
	"time"
)

func (b *Block) generateHash() {
	bytes, _ := json.Marshal((b.Data))
	data := string(b.Position) + b.TimeStamp + string(bytes) + b.PrevHash

	hash := sha256.New()
	hash.Write([]byte(data))
	b.Hash = hex.EncodeToString(hash.Sum(nil))
}

func createBlock(prevBlock *Block, getItem getNFT) *Block {
	block := &Block{}
	block.Position = prevBlock.Position + 1
	block.TimeStamp = time.Now().String()
	block.Data = getItem
	block.PrevHash = prevBlock.Hash
	block.generateHash()

	return block

}

func (bc *Blockchain) AddBlock(data getNFT) {
	prevBlock := bc.blocks[len(bc.blocks)-1]
	block := createBlock(prevBlock, data)

	if validBlock(block, prevBlock) {
		bc.blocks = append(bc.blocks, block)
	}
}

func GenesisBlock() *Block {
	return createBlock(&Block{}, getNFT{IsGenesis: true})
}

func NewBlockchain() *Blockchain {
	return &Blockchain{[]*Block{GenesisBlock()}}
}

func validBlock(block, prevBlock *Block) bool {
	if prevBlock.Hash != block.PrevHash {
		return false
	}
	if !block.validateHash(block.Hash) {
		return false
	}
	if prevBlock.Position+1 != block.Position {
		return false
	}
	return true
}

func (b *Block) validateHash(hash string) bool {
	b.generateHash()
	if b.Hash != hash {
		return false
	}
	return true
}

func getBlockchain(w http.ResponseWriter, r *http.Request) {
	jbytes, err := json.MarshalIndent(BlockChain.blocks, "", " ")
	if err != nil {
		w.WriteHeader(http.StatusInternalServerError)
		json.NewEncoder(w).Encode(err)
		return
	}
	io.WriteString(w, string(jbytes))

}

func writeBlock(w http.ResponseWriter, r *http.Request) {
	var getItem getNFT

	if err := json.NewDecoder(r.Body).Decode(&getItem); err != nil {
		w.WriteHeader(http.StatusInternalServerError)
		log.Printf("Unable to write the block %v", err)
		w.Write([]byte("Unable to write block"))
		return

	}

	BlockChain.AddBlock(getItem)
	resp, err := json.MarshalIndent(getItem, "", " ")
	if err != nil {
		w.WriteHeader(http.StatusInternalServerError)
		log.Printf("could not marshal payload: %v", err)
		w.Write([]byte("could not write block"))
		return
	}
	w.WriteHeader(http.StatusOK)
	w.Write(resp)

}

func newNFT(w http.ResponseWriter, r *http.Request) {
	var nft NFT

	if err := json.NewDecoder(r.Body).Decode(&nft); err != nil {
		w.WriteHeader(http.StatusInternalServerError)
		log.Printf("Unable to create %v.", err)
		w.Write([]byte("Unable to create the NFT"))
		return
	}

	h := md5.New()
	io.WriteString(h, nft.Metadata+nft.CreatedOn)
	nft.TokenID = fmt.Sprintf("%x", h.Sum(nil))

	resp, err := json.MarshalIndent(nft, "", " ")
	if err != nil {
		w.WriteHeader(http.StatusInternalServerError)
		log.Printf("Unable to marshal payload: %v", err)
		w.Write([]byte("Unable to save NFT Metadata"))
		return
	}

	w.WriteHeader(http.StatusOK)
	w.Write(resp)

}
