import { createClient, SupabaseClient } from '@supabase/supabase-js';

const supabaseUrl = import.meta.env.VITE_SUPABASE_URL || '';
const supabaseAnonKey = import.meta.env.VITE_SUPABASE_ANON_KEY || '';

// Validate the URL before creating the client to prevent a crash
function isValidUrl(url: string): boolean {
  try {
    new URL(url);
    return true;
  } catch {
    return false;
  }
}

let supabase: SupabaseClient;

if (isValidUrl(supabaseUrl) && supabaseAnonKey) {
  supabase = createClient(supabaseUrl, supabaseAnonKey);
} else {
  console.warn(
    '[ASKME] Supabase credentials not configured. Auth features will be unavailable. ' +
    'Set VITE_SUPABASE_URL and VITE_SUPABASE_ANON_KEY in frontend/.env'
  );
  // Create a dummy client pointing to a placeholder so the app can render
  // This will fail on actual auth calls, which is the correct behavior
  supabase = createClient('https://placeholder.supabase.co', 'placeholder-key');
}

export { supabase };
