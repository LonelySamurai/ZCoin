package main

import (
	"fmt"
)

type Delegates struct {
	Delegate string
	Votes    int
	IsActive bool
}

type Voters struct {
	Voter string
	Stake int
}

type Transaction struct {
	From   string
	To     string
	Amount int
}

var currentDelegateIndex int

func (dl *Delegates) ElectDelegates() {

	var sortedVoters []Voters
	for _, voter := range dl.Delegate {
		sortedVoters = append(sortedVoters, voter.Voter)
	}

	for i := 0; i < len(sortedVoters)-1; i++ {
		for j := 0; j < len(sortedVoters)-i-1; j++ {
			if sortedVoters[j].Stake < sortedVoters[j+1].Stake {
				sortedVoters[j], sortedVoters[j+1] = sortedVoters[j+1], sortedVoters[j]
			}
		}
	}

	for i := 0; i < 3; i++ {
		voter := sortedVoters[i]
		dl.Delegate[voter.Voter] = &Delegates{
			Voter:    voter.Voter,
			Votes:    voter.Stake,
			IsActive: true,
		}
	}
}

func DPoS() {

	BlockChain = NewBlockchain()

	//BlockChain.ElectDelegates()

	fmt.Println("Delegates after election:")
	for _, delegate := range BlockChain.blocks {
		fmt.Printf("Delegate: %s, Votes: %d\n", delegate.Name, delegate.Votes)
	}

	//BlockChain.AddBlock("User 1")

	for _, block := range BlockChain.blocks {
		fmt.Printf("Block #%d\n", block.Position)
		fmt.Printf("Timestamp: %s\n", block.TimeStamp)
		fmt.Printf("Data: %s\n", block.Data)
		fmt.Printf("Hash: %s\n", block.Hash)
	}
}
