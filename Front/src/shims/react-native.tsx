import React from 'react';

type CommonProps = React.HTMLAttributes<HTMLElement> & {
  className?: string;
  style?: React.CSSProperties;
  children?: React.ReactNode;
};

export const Platform = { OS: 'web' };

export const Alert = {
  alert: (title: string, message?: string) => {
    window.alert(message ? `${title}\n${message}` : title);
  },
};

export const View: React.FC<CommonProps> = ({ children, ...props }) => <div {...props}>{children}</div>;

export const Text: React.FC<CommonProps & { numberOfLines?: number; ellipsizeMode?: string }> = ({
  children,
  numberOfLines,
  ...props
}) => (
  <span
    {...props}
    style={{
      ...(props.style || {}),
      ...(numberOfLines
        ? {
            overflow: 'hidden',
            display: '-webkit-box',
            WebkitLineClamp: numberOfLines,
            WebkitBoxOrient: 'vertical' as any,
          }
        : {}),
    }}
  >
    {children}
  </span>
);

export const ScrollView: React.FC<
  CommonProps & {
    horizontal?: boolean;
    contentContainerStyle?: React.CSSProperties;
    contentContainerClassName?: string;
    showsVerticalScrollIndicator?: boolean;
    showsHorizontalScrollIndicator?: boolean;
  }
> = ({ children, horizontal, contentContainerStyle, contentContainerClassName, style, ...props }) => (
  <div
    {...props}
    style={{
      overflowX: horizontal ? 'auto' : 'hidden',
      overflowY: horizontal ? 'hidden' : 'auto',
      ...(style || {}),
    }}
  >
    <div className={contentContainerClassName} style={contentContainerStyle}>
      {children}
    </div>
  </div>
);

export const TouchableOpacity: React.FC<
  Omit<React.ButtonHTMLAttributes<HTMLButtonElement>, 'onPress'> & {
    onPress?: () => void | Promise<void>;
    android_ripple?: any;
  }
> = ({ children, onPress, type, ...props }) => (
  <button
    type={type || 'button'}
    onClick={() => {
      void onPress?.();
    }}
    {...props}
  >
    {children}
  </button>
);

export const Pressable = TouchableOpacity;

export const TextInput: React.FC<
  Omit<React.InputHTMLAttributes<HTMLInputElement>, 'onChangeText'> & {
    onChangeText?: (value: string) => void;
    secureTextEntry?: boolean;
    placeholderTextColor?: string;
  }
> = ({ onChangeText, secureTextEntry, ...props }) => (
  <input
    {...props}
    type={secureTextEntry ? 'password' : props.type}
    onChange={(e) => {
      onChangeText?.(e.target.value);
      props.onChange?.(e);
    }}
  />
);

export const ActivityIndicator: React.FC<{ size?: 'small' | 'large'; color?: string }> = ({ size = 'small', color = '#3b82f6' }) => {
  const side = size === 'large' ? 32 : 18;
  return (
    <svg className="animate-spin" style={{ width: side, height: side, color }} xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"></path>
    </svg>
  );
};

export const Image: React.FC<React.ImgHTMLAttributes<HTMLImageElement> & { source?: any }> = ({ source, ...props }) => {
  const src = typeof source === 'string' ? source : source?.uri;
  return <img src={src} {...props} />;
};

export const ImageBackground: React.FC<CommonProps & { source?: any; imageStyle?: any }> = ({
  source,
  style,
  imageStyle,
  children,
  ...props
}) => {
  const backgroundImage = typeof source === 'string' ? source : source?.uri;
  const resizeMode = imageStyle?.resizeMode;

  return (
    <div
      {...props}
      style={{
        backgroundImage: backgroundImage ? `url(${backgroundImage})` : undefined,
        backgroundSize: resizeMode === 'contain' ? 'contain' : 'cover',
        backgroundRepeat: 'no-repeat',
        backgroundPosition: 'center',
        ...(style || {}),
      }}
    >
      {children}
    </div>
  );
};
