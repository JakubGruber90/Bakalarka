export interface Message {
    text: string,
    role: 'assistant' | 'user'
}

export interface Citation {
    content: string,
    title: string,
    url: string,
    filepath: string,
    chunk_id: string
}