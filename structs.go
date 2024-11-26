package main

type Blockchain struct {
	blocks []*Block
}

type Deelegates struct {
	Delegates map[string]*Delegates
	Voters    map[string]*Voters
}

type Block struct {
	Position  int
	Data      getNFT
	TimeStamp string
	Hash      string
	PrevHash  string
}

type getNFT struct {
	NFTID     string `json:"nft_id"`
	User      string `json:"user"`
	GetDate   string `json:"get_date"`
	IsGenesis bool   `json:"is_genesis"`
}

type NFT struct {
	TokenID   string `json:"id"`
	Name      string `json:"name"`
	Owner     string `json:"owner"`
	CreatedOn string `json:"created_on"`
	Metadata  string `json:"metadata"`
}
