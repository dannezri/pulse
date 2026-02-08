import "jsr:@supabase/functions-js/edge-runtime.d.ts";
import { createClient } from "jsr:@supabase/supabase-js@2";

const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
};

/**
 * Edge Function pour synchroniser automatiquement l'historique des médicaments
 * Exécutée quotidiennement par pg_cron à minuit
 */
Deno.serve(async (req: Request) => {
  // Handle CORS preflight
  if (req.method === 'OPTIONS') {
    return new Response('ok', { headers: corsHeaders });
  }

  try {
    console.log('🚀 Starting daily medication history sync...');

    // Create Supabase client with service role
    const supabaseUrl = Deno.env.get('SUPABASE_URL')!;
    const supabaseServiceKey = Deno.env.get('SUPABASE_SERVICE_ROLE_KEY')!;
    
    const supabase = createClient(supabaseUrl, supabaseServiceKey);

    // 1. Récupérer tous les utilisateurs qui ont des médicaments actifs
    const { data: users, error: usersError } = await supabase
      .from('user_medications')
      .select('user_id')
      .eq('is_active', true)
      .order('user_id');

    if (usersError) {
      console.error('❌ Error fetching users:', usersError);
      throw usersError;
    }

    // Dédupliquer les user_ids
    const uniqueUserIds = [...new Set(users?.map(u => u.user_id) || [])];
    console.log(`📊 Found ${uniqueUserIds.length} users with active medications`);

    // 2. Pour chaque utilisateur, exécuter la fonction de génération d'historique
    const results = [];
    let successCount = 0;
    let errorCount = 0;

    for (const userId of uniqueUserIds) {
      try {
        console.log(`📝 Processing user: ${userId}`);

        // Appeler la fonction SQL pour générer l'historique du jour
        const { data, error } = await supabase.rpc('auto_populate_medication_history', {
          p_user_id: userId,
        });

        if (error) {
          console.error(`❌ Error for user ${userId}:`, error);
          errorCount++;
          results.push({
            userId,
            status: 'error',
            error: error.message,
          });
        } else {
          console.log(`✅ Success for user ${userId}: ${data?.length || 0} medications processed`);
          successCount++;
          results.push({
            userId,
            status: 'success',
            medications: data,
          });
        }
      } catch (err) {
        console.error(`❌ Exception for user ${userId}:`, err);
        errorCount++;
        results.push({
          userId,
          status: 'error',
          error: err.message,
        });
      }
    }

    console.log(`🎉 Sync completed: ${successCount} success, ${errorCount} errors`);

    // 3. Logger le résultat dans une table d'audit (optionnel)
    const syncLog = {
      sync_date: new Date().toISOString(),
      users_processed: uniqueUserIds.length,
      success_count: successCount,
      error_count: errorCount,
      results: results,
    };

    console.log('📊 Sync summary:', syncLog);

    return new Response(
      JSON.stringify({
        success: true,
        summary: {
          users_processed: uniqueUserIds.length,
          success_count: successCount,
          error_count: errorCount,
        },
        results: results,
        timestamp: new Date().toISOString(),
      }),
      {
        headers: {
          ...corsHeaders,
          'Content-Type': 'application/json',
        },
      }
    );
  } catch (error) {
    console.error('❌ Fatal error:', error);
    
    return new Response(
      JSON.stringify({
        success: false,
        error: error.message,
        timestamp: new Date().toISOString(),
      }),
      {
        status: 500,
        headers: {
          ...corsHeaders,
          'Content-Type': 'application/json',
        },
      }
    );
  }
});
