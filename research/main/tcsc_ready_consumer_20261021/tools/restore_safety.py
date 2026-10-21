from pathlib import Path
import argparse,json,msvcrt,sys
ROOT=Path(__file__).resolve().parents[1]
ADMIN=ROOT.parent/'RESEARCH_ARCHIVE_FULL_BACKUP_20261021'
sys.path.insert(0,str(ADMIN))
import independent_restore,restore_evidence
selection=json.loads((ROOT/'audit/SAFETY_RESTORE_SELECTION.json').read_text())
ref=json.loads((ADMIN/'ROOT_CHECKPOINT_VERIFIED_RECEIPT.json').read_text())
lock=(ADMIN/'local_only/archive_upload.lock').open('r+b');msvcrt.locking(lock.fileno(),msvcrt.LK_NBLCK,1)
class Limited(independent_restore.Reader):
    consumed=0
    def download(self,file_id,expected_sha256):
        info=self.api_json('b2_get_file_info',{'fileId':file_id})
        self.consumed+=info['contentLength']
        if self.consumed>1024**3:raise RuntimeError('SAFETY_RESTORE_1GIB_LIMIT')
        return super().download(file_id,expected_sha256)
restore_evidence.Reader=Limited
restore_evidence.main(argparse.Namespace(root_file_id=ref['root_file_id'],root_sha256=ref['root_sha256'],
    destination=str(ROOT/'input/archived_safety'),evidence_id=['sha256:'+r['sha256'] for r in selection],
    all=False,root_id=['WIN_TASK'],prompt_key=False))
