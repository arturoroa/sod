import React from 'react';

type PickerProps = React.SelectHTMLAttributes<HTMLSelectElement> & {
  selectedValue?: string;
  onValueChange?: (value: any, index: number) => void;
};

type PickerItemProps = {
  label: string;
  value: string;
};

const PickerComponent: React.FC<PickerProps> & { Item: React.FC<PickerItemProps> } = ({
  children,
  selectedValue,
  onValueChange,
  ...props
}) => {
  return (
    <select
      {...props}
      value={selectedValue}
      onChange={(e) => {
        onValueChange?.(e.target.value, e.target.selectedIndex);
        props.onChange?.(e);
      }}
    >
      {children}
    </select>
  );
};

PickerComponent.Item = ({ label, value }) => <option value={value}>{label}</option>;

export const Picker = PickerComponent;
