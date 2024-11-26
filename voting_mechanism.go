package main

import "fmt"

func (bc *Deelegates) VoteForDelegate(voterName, delegateName string) error {
	voter, exists := bc.Voters[voterName]
	if !exists {
		return fmt.Errorf("Voter does not exist")
	}

	delegate, exists := bc.Delegates[delegateName]
	if !exists {
		return fmt.Errorf("Delegate does not exist")
	}

	delegate.Votes += voter.Stake
	return nil
}

func (bc *Deelegates) ProposeNextBlock() {

	delegates := make([]*Delegates, 0, len(bc.Delegates))
	for _, delegate := range bc.Delegates {
		if delegate.IsActive {
			delegates = append(delegates, delegate)
		}
	}

	delegate := delegates[currentDelegateIndex]
	//blockData := fmt.Sprintf("Block proposed by %s", delegate.Name)
	//bc.AddBlock(blockData)
	fmt.Println(delegate)

	currentDelegateIndex = (currentDelegateIndex + 1) % len(delegates)
}
