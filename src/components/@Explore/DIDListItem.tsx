import React from 'react';
import { createUseStyles } from 'react-jss';
import { FileDIDItemDetails } from './FileDIDItemDetails';
import { CollectionDIDItemDetails } from './CollectionDIDItemDetails';
import { toHumanReadableSize } from '../../utils/Helpers';
import { ListAttachedFilesPopover } from './ListAttachedFilesPopover';

const useStyles = createUseStyles({
  listItemContainer: {
    borderBottom: '1px solid #E0E0E0',
    overflow: 'hidden',
    boxSizing: 'border-box'
  },
  listItem: {
    display: 'flex',
    flexDirection: 'row',
    fontSize: '9pt',
    alignItems: 'center',
    padding: '8px 16px 8px 16px',
    cursor: 'pointer'
  },
  listItemCollapsed: {
    extend: 'listItem',
    '&:hover': {
      backgroundColor: '#eeeeee'
    }
  },
  listItemExpanded: {
    extend: 'listItem',
    backgroundColor: '#F8F8F8'
  },
  textContainer: {
    flex: 1,
    textOverflow: 'ellipsis',
    overflow: 'hidden'
  },
  iconContainer: {
    lineHeight: 0,
    marginRight: '8px'
  },
  icon: {
    fontSize: '16px',
    verticalAlign: 'middle'
  },
  fileIcon: {
    extend: 'icon',
    color: '#66B100'
  },
  containerIcon: {
    extend: 'icon',
    color: '#5DC0FD'
  },
  datasetIcon: {
    extend: 'icon',
    color: '#FFB100'
  },
  sizeContainer: {
    color: '#808080'
  },
  listFilesIcon: {
    extend: 'icon',
    color: '#2196F3',
    cursor: 'pointer'
  }
});

export interface DIDItem {
  did: string;
  size?: number;
  type: 'dataset' | 'container' | 'file';
  onClick?: { (): any };
  expand?: boolean;
  style?: any;
}

export const DIDListItem: React.FC<DIDItem> = ({ did, size, type, onClick, expand, style }) => {
  const classes = useStyles();

  const handleViewFilesClick = (e: React.MouseEvent<HTMLDivElement, MouseEvent>) => {
    e.stopPropagation();
  };

  return (
    <div className={classes.listItemContainer} style={style}>
      <div className={expand ? classes.listItemExpanded : classes.listItemCollapsed} onClick={onClick}>
        <div className={classes.iconContainer}>
          {type === 'file' && <i className={`${classes.fileIcon} material-icons`}>attachment</i>}
          {type === 'container' && <i className={`${classes.containerIcon} material-icons`}>folder</i>}
          {type === 'dataset' && <i className={`${classes.datasetIcon} material-icons`}>folder_open</i>}
        </div>
        <div className={classes.textContainer}>{did}</div>
        {type === 'file' && !!size && <div className={classes.sizeContainer}>{toHumanReadableSize(size)}</div>}
        {(type === 'container' || type === 'dataset') && (
          <div onClick={handleViewFilesClick}>
            <ListAttachedFilesPopover did={did}>
              <i className={`${classes.listFilesIcon} material-icons`}>visibility</i>
            </ListAttachedFilesPopover>
          </div>
        )}
      </div>
      {!!expand && type === 'file' && <FileDIDItemDetails did={did} />}
      {!!expand && (type === 'container' || type === 'dataset') && <CollectionDIDItemDetails did={did} />}
    </div>
  );
};
