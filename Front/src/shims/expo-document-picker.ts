export type DocumentPickerAsset = {
  uri: string;
  name: string;
  mimeType?: string;
  file?: File;
};

export type DocumentPickerResult = {
  canceled: boolean;
  assets: DocumentPickerAsset[];
};

const toAccept = (types?: string[]) => {
  if (!types || types.length === 0) {
    return '*/*';
  }
  return types.join(',');
};

export const getDocumentAsync = async ({ type }: { type?: string[] }): Promise<DocumentPickerResult> => {
  return new Promise((resolve) => {
    const input = document.createElement('input');
    input.type = 'file';
    input.accept = toAccept(type);
    input.onchange = () => {
      const file = input.files?.[0];
      if (!file) {
        resolve({ canceled: true, assets: [] });
        return;
      }

      resolve({
        canceled: false,
        assets: [
          {
            uri: URL.createObjectURL(file),
            name: file.name,
            mimeType: file.type,
            file,
          },
        ],
      });
    };
    input.click();
  });
};

export default { getDocumentAsync };
