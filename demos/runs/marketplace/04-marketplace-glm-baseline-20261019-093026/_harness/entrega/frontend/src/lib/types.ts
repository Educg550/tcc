export interface Seller {
  id: number;
  name: string;
}

export interface Listing {
  id: number;
  is_favorite?: boolean;
  title: string;
  description: string;
  price_cents: number;
  stock: number;
  category: string;
  condition: string;
  city: string;
  image_url: string | null;
  status: string;
  seller: Seller;
  created_at: string | null;
  seller_listings?: Listing[];
}

export interface Paginated<T> {
  items: T[];
  total: number;
  page: number;
  limit: number;
}

export interface Review {
  id: number;
  order_id: number;
  listing_id: number;
  buyer_id: number;
  buyer_name: string;
  rating: number;
  comment: string;
  created_at: string | null;
}

export interface Conversation {
  id: number;
  listing_id: number;
  listing_title: string;
  buyer_id: number;
  seller_id: number;
  other_user: Seller;
  created_at: string | null;
}

export interface Message {
  id: number;
  conversation_id: number;
  sender_id: number;
  content: string;
  created_at: string | null;
}

export interface Order {
  id: number;
  listing_id: number;
  listing_title: string;
  buyer_id: number;
  seller_id: number;
  buyer_name: string;
  seller_name: string;
  quantity: number;
  unit_price_cents: number;
  total_cents: number;
  address: string;
  status: string;
  created_at: string | null;
  updated_at: string | null;
}
