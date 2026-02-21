-- Create documents storage bucket
INSERT INTO storage.buckets (id, name, public) VALUES ('documents', 'documents', false);

-- Policy: users can upload files to their own folder
CREATE POLICY "users_upload_own_documents" ON storage.objects FOR INSERT
    WITH CHECK (bucket_id = 'documents' AND (storage.foldername(name))[1] = auth.uid()::text);

-- Policy: users can read their own files
CREATE POLICY "users_read_own_documents" ON storage.objects FOR SELECT
    USING (bucket_id = 'documents' AND (storage.foldername(name))[1] = auth.uid()::text);

-- Policy: users can delete their own files
CREATE POLICY "users_delete_own_documents" ON storage.objects FOR DELETE
    USING (bucket_id = 'documents' AND (storage.foldername(name))[1] = auth.uid()::text);
