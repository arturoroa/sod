import React from 'react';

type WebViewProps = {
  source?: {
    html?: string;
    uri?: string;
  };
  style?: React.CSSProperties;
};

const WebView: React.FC<WebViewProps> = ({ source, style }) => {
  if (source?.uri) {
    return <iframe src={source.uri} style={{ width: '100%', height: '100%', border: 'none', ...style }} allowFullScreen />;
  }

  return <iframe srcDoc={source?.html || ''} style={{ width: '100%', height: '100%', border: 'none', ...style }} allowFullScreen />;
};

export { WebView };
export default WebView;
