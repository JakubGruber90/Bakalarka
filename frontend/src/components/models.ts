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

export interface Question {
    id: number,
    text: string,
    answer: string,
    ground_truth: string,
    faithfulness: number,
    answer_relevancy: number,
    context_recall: number,
    context_precision: number,
    search_type: string,
    eval: boolean
}